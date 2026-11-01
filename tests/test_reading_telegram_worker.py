"""Editorial product resolution and same-day delivery preparation; no network."""

from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reading_telegram_worker import editorial_product, verified_snapshot


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

    def test_old_books_do_not_generate_editorial_requests(self):
        book = {**self.book, "fecha_publicacion": "2009-06-01"}
        with patch("reading_telegram_worker.editorial_product") as parser:
            result, report = verified_snapshot(
                {"libros": [book]}, self.intake, date(2026, 11, 1), lambda *_: self.html
            )
        parser.assert_not_called()
        self.assertEqual(report["checked"], 0)


if __name__ == "__main__":
    unittest.main()
