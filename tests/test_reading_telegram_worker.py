"""Editorial product resolution and same-day delivery preparation; no network."""

from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import reading_telegram_worker
from reading_telegram_worker import (
    MAX_MAIN_JSON_BYTES,
    editorial_product,
    main_json,
    verified_snapshot,
)

DATA = Path(__file__).resolve().parents[1] / "data"


class EditorialTelegramTests(unittest.TestCase):
    def setUp(self):
        self.book = {
            "id": "one",
            "estado": "publicado",
            "isbn13": "9788401042751",
            "titulo": "Libro",
            "autores": ["Autora"],
            "fecha_publicacion": "2026-11-01",
            "fuente_publicacion_url": "https://www.penguinlibros.com/es/novela/1-libro-9788401042751",
        }
        self.source = {
            "id": "penguin-es",
            "provider": "penguin",
            "enabled": True,
            "hosts": ["www.penguinlibros.com"],
        }
        self.intake = {"sources": [self.source], "amazon_partner_tag": "davidporto-21"}
        self.edition = {
            "isbn13": self.book["isbn13"],
            "titulo": "Libro",
            "autores": ["Autora"],
            "fecha_publicacion_edicion": "2026-11-01",
        }
        self.html = (
            '<a href="https://www.amazon.es/dp/B0HC7BJS7K?tag=editorial-21">Amazon</a>'
        )

    def test_editorial_edition_resolves_without_following_amazon(self):
        with patch(
            "reading_telegram_worker.penguin_edition", return_value=self.edition
        ):
            result, report = verified_snapshot(
                {"libros": [self.book]},
                self.intake,
                date(2026, 11, 1),
                lambda u, s: self.html,
            )
        self.assertEqual(report["resolved"], 1)
        self.assertEqual(
            result["libros"][0]["url_amazon_afiliada"],
            "https://www.amazon.es/dp/B0HC7BJS7K?tag=davidporto-21",
        )
        self.assertNotIn("url_amazon_afiliada", self.book)

    def test_search_ambiguity_and_hostile_product_are_not_accepted(self):
        for document in [
            '<a href="https://www.amazon.es/s?k=9788401042751">Amazon</a>',
            '<a href="https://www.amazon.es.evil/dp/B0HC7BJS7K">Amazon</a>',
            self.html + '<a href="https://www.amazon.es/dp/B0HC3Y2XLT">Amazon</a>',
        ]:
            with (
                self.subTest(document=document),
                patch(
                    "reading_telegram_worker.penguin_edition", return_value=self.edition
                ),
            ):
                with self.assertRaises(ValueError):
                    editorial_product(
                        document,
                        self.book["fuente_publicacion_url"],
                        self.book,
                        self.source,
                    )

    def test_isbn_and_author_mismatch_fail_closed(self):
        for field, value in [("isbn13", "9788498382372"), ("autores", ["Otra autora"])]:
            edition = {**self.edition, field: value}
            with patch("reading_telegram_worker.penguin_edition", return_value=edition):
                with self.assertRaises(ValueError):
                    editorial_product(
                        self.html,
                        self.book["fuente_publicacion_url"],
                        self.book,
                        self.source,
                    )

    def test_postponed_book_keeps_actual_date(self):
        edition = {**self.edition, "fecha_publicacion_edicion": "2026-11-05"}
        with patch("reading_telegram_worker.penguin_edition", return_value=edition):
            result, _ = verified_snapshot(
                {"libros": [self.book]},
                self.intake,
                date(2026, 11, 1),
                lambda u, s: self.html,
            )
        self.assertEqual(result["libros"][0]["fecha_publicacion"], "2026-11-05")

    def test_source_failure_blocks_stale_due_book(self):
        book = {
            **self.book,
            "url_amazon_afiliada": "https://www.amazon.es/dp/B0HC7BJS7K?tag=davidporto-21",
        }

        def fail(*args):
            raise OSError("offline")

        result, report = verified_snapshot(
            {"libros": [book]}, self.intake, date(2026, 11, 1), fail
        )
        self.assertEqual(
            result["libros"][0]["estado"], "pendiente_verificacion_telegram"
        )
        self.assertEqual(len(report["pending"]), 1)

    def test_amazon_intake_book_uses_its_product_page_without_requests(self):
        book = {
            **self.book,
            "fuente_publicacion_url": "https://www.amazon.es/dp/8415955626",
            "precios_amazon_revision": "2026-11-01",
        }

        def no_fetch(*args):
            raise AssertionError("no request expected")

        result, report = verified_snapshot(
            {"libros": [book]}, self.intake, date(2026, 11, 1), no_fetch
        )
        self.assertEqual(report["resolved"], 1)
        self.assertEqual(
            result["libros"][0]["url_amazon_afiliada"],
            "https://www.amazon.es/dp/8415955626?tag=davidporto-21",
        )

    def test_stale_or_search_amazon_source_stays_pending(self):
        for extra in [
            {"fuente_publicacion_url": "https://www.amazon.es/dp/8415955626",
             "precios_amazon_revision": "2026-10-20"},
            {"fuente_publicacion_url": "https://www.amazon.es/s?k=9788415955627",
             "precios_amazon_revision": "2026-11-01"},
        ]:
            with self.subTest(extra=extra):
                result, report = verified_snapshot(
                    {"libros": [{**self.book, **extra}]},
                    self.intake,
                    date(2026, 11, 1),
                    lambda *_: self.html,
                )
                self.assertEqual(report["resolved"], 0)
                self.assertEqual(
                    result["libros"][0]["estado"], "pendiente_verificacion_telegram"
                )

    def test_editorial_without_amazon_link_uses_fresh_print_offer(self):
        def offer(fmt, asin, checked):
            return {
                "formato": fmt,
                "fuente_url": f"https://www.amazon.es/dp/{asin}",
                "fecha_verificacion": checked,
            }

        cases = [
            ([offer("tapa-blanda", "8401042751", "2026-10-31")], "8401042751"),
            ([offer("tapa-blanda", "8401042751", "2026-10-25")], None),
            ([offer("ebook", "B0HC7BJS7K", "2026-11-01")], None),
            (
                [
                    offer("tapa-blanda", "8401042751", "2026-11-01"),
                    offer("tapa-dura", "8401042760", "2026-11-01"),
                ],
                None,
            ),
        ]
        for offers, expected in cases:
            with self.subTest(offers=offers), patch(
                "reading_telegram_worker.penguin_edition", return_value=self.edition
            ):
                result, report = verified_snapshot(
                    {"libros": [{**self.book, "formatos_compra": offers}]},
                    self.intake,
                    date(2026, 11, 1),
                    lambda u, s: "<p>Sin enlaces</p>",
                )
                if expected:
                    self.assertEqual(report["verified"][0]["asin"], expected)
                else:
                    self.assertEqual(report["resolved"], 0)

    def test_books_seeded_from_todostuslibros_are_verified_on_its_record(self):
        url = "https://www.todostuslibros.com/libros/libro_9788401042751"
        book = {
            **self.book,
            "fuente_publicacion_url": url,
            "formatos_compra": [
                {
                    "formato": "tapa-blanda",
                    "fuente_url": "https://www.amazon.es/dp/8401042751",
                    "fecha_verificacion": "2026-10-31",
                }
            ],
        }
        source = {
            "id": "todostuslibros-altas",
            "provider": "todostuslibros",
            "enabled": True,
            "hosts": ["www.todostuslibros.com"],
        }
        with patch("reading_telegram_worker.ttl_edition", return_value=self.edition):
            _, report = verified_snapshot(
                {"libros": [book]},
                {**self.intake, "sources": [source]},
                date(2026, 11, 1),
                lambda u, s: "<p>Ficha CEGAL</p>",
            )
        self.assertEqual(report["verified"][0]["asin"], "8401042751")

    def test_budget_goes_to_todays_books_first(self):
        books = [
            {**self.book, "id": d, "fecha_publicacion": d}
            for d in ("2026-11-30", "2026-10-30", "2026-11-02", "2026-11-01", "2026-10-31")
        ]

        def fetch(url, source):
            raise OSError("offline")

        with patch("reading_telegram_worker.editorial_product"):
            _, report = verified_snapshot(
                {"libros": books}, self.intake, date(2026, 11, 1), fetch
            )
        order = [p["id"] for p in report["pending"]]
        self.assertEqual(
            order, ["2026-11-01", "2026-11-02", "2026-11-30", "2026-10-31", "2026-10-30"]
        )

    def test_old_books_do_not_generate_editorial_requests(self):
        book = {**self.book, "fecha_publicacion": "2009-06-01"}
        with patch("reading_telegram_worker.editorial_product") as parser:
            result, report = verified_snapshot(
                {"libros": [book]}, self.intake, date(2026, 11, 1), lambda *_: self.html
            )
        parser.assert_not_called()
        self.assertEqual(report["checked"], 0)


class MainJsonSizeGuardTests(unittest.TestCase):
    """The nightly publisher fetches main's data files; its sanity cap must stay above
    the real, growing catalogue. On 2026-11-10 the catalogue crossed 8 MB and the fixed
    cap rejected it, turning every scheduled cycle red. This gate goes red first, in the
    local gate, while there is still runway to react."""

    class _Resp:
        def __init__(self, content, status=200):
            self.content = content
            self.status_code = status

        def json(self):
            return {"libros": []}

    def test_real_data_files_fit_under_cap_with_margin(self):
        # 75 % of the cap leaves weeks of ingesta runway before the publisher would break.
        headroom = int(MAX_MAIN_JSON_BYTES * 0.75)
        for name in ("reading-catalogue.json", "reading-intake-config.json"):
            size = (DATA / name).stat().st_size
            self.assertLessEqual(
                size,
                headroom,
                f"{name} ({size} B) nears the main_json cap ({MAX_MAIN_JSON_BYTES} B): "
                "raise MAX_MAIN_JSON_BYTES before the scheduled publisher rejects it.",
            )

    def test_real_catalogue_size_is_accepted_by_main_json(self):
        size = (DATA / "reading-catalogue.json").stat().st_size
        resp = self._Resp(b"x" * size)
        with patch.object(reading_telegram_worker.requests, "get", return_value=resp):
            self.assertEqual(main_json("reading-catalogue.json"), {"libros": []})

    def test_oversized_or_error_response_is_rejected(self):
        oversized = self._Resp(b"x" * (MAX_MAIN_JSON_BYTES + 1))
        not_found = self._Resp(b"{}", status=404)
        for resp in (oversized, not_found):
            with patch.object(
                reading_telegram_worker.requests, "get", return_value=resp
            ):
                with self.assertRaises(ValueError):
                    main_json("reading-catalogue.json")


class CoverResolverTests(unittest.TestCase):
    @staticmethod
    def response(kind, size, code=200):
        from unittest.mock import Mock
        return Mock(status_code=code, headers={"Content-Type": kind}, content=b"x" * size)

    def test_real_amazon_cover_replaces_typographic_and_is_reported_once(self):
        from reading_telegram_worker import cover_resolver
        fixes = []
        get = lambda url, **kw: self.response("image/jpeg", 40000)
        resolve = cover_resolver(fixes, get=get, fetch_json=lambda url: {})
        book = {"id": "b", "title": "Libro", "asin": "8401042755", "isbn13": "9788401042751",
                "generated_cover": True}
        url = resolve(book)
        self.assertIn("/images/P/8401042755.01.", url)
        self.assertEqual(resolve(book), url)
        self.assertEqual(fixes, [{"id": "b", "title": "Libro", "source": "Amazon",
                                  "verdict": "fallo nuestro: había portada real"}])
        self.assertIsNone(resolve({**book, "id": "c", "generated_cover": False}))

    def test_placeholder_everywhere_keeps_our_cover(self):
        from reading_telegram_worker import cover_resolver
        fixes = []
        get = lambda url, **kw: (self.response("image/gif", 800) if "amazon" in url
                                 else self.response("text/html", 0, 404))
        resolve = cover_resolver(fixes, get=get, fetch_json=lambda url: {})
        book = {"id": "p", "title": "Peces voladores", "asin": "B0ABCDEFGH",
                "isbn13": "9788401042751", "generated_cover": True}
        self.assertIsNone(resolve(book))
        self.assertEqual(fixes[0]["verdict"], "sin portada real: tipográfica")

    def test_cycle_waits_until_1130_without_any_request(self):
        import tempfile
        from datetime import datetime
        from zoneinfo import ZoneInfo
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(reading_telegram_worker, "main_json", side_effect=AssertionError), \
                patch.object(reading_telegram_worker, "datetime") as clock:
            clock.now.return_value = datetime(2026, 11, 10, 9, 0, tzinfo=ZoneInfo("Europe/Madrid"))
            report = reading_telegram_worker.cycle(Path(tmp), live=True)
        self.assertEqual(report["status"], "waiting")


if __name__ == "__main__":
    unittest.main()
