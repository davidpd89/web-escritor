"""Offline Telegram contracts using the native reading catalogue schema."""

import copy
from contextlib import closing
from datetime import date
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reading_telegram import from_reading_catalogue, run, send, smoke, cover_url


class ReadingTelegramTests(unittest.TestCase):
    def test_only_verified_site_cover_is_used(self):
        book = {
            "portada_edicion_verificada": True,
            "portada_local": "/assets/reading-covers/book.webp",
        }
        self.assertEqual(
            cover_url(book),
            "https://davidportodiaz.com/assets/reading-covers/book.webp",
        )
        for path in [
            "//evil.example/book.jpg",
            "/assets/reading-covers/../private.png",
            "https://evil.example/book.jpg",
        ]:
            self.assertIsNone(cover_url({**book, "portada_local": path}))
        self.assertIsNone(cover_url({**book, "portada_edicion_verificada": False}))

    def test_photo_transport_uses_caption_and_returns_message_id(self):
        post = Mock(
            return_value=Mock(
                status_code=200, json=lambda: {"ok": True, "result": {"message_id": 99}}
            )
        )
        with patch("reading_telegram.requests.post", post):
            self.assertEqual(
                send(
                    "secret",
                    "@test",
                    "caption",
                    "https://davidportodiaz.com/assets/reading-covers/book.webp",
                ),
                ("sent", 99),
            )
        self.assertTrue(post.call_args.args[0].endswith("/sendPhoto"))
        self.assertEqual(post.call_args.kwargs["json"]["caption"], "caption")

    def test_rejected_photo_falls_back_to_text(self):
        responses = [
            Mock(status_code=400, json=lambda: {"ok": False}),
            Mock(
                status_code=200,
                json=lambda: {"ok": True, "result": {"message_id": 100}},
            ),
        ]
        with patch("reading_telegram.requests.post", side_effect=responses) as post:
            self.assertEqual(
                send("secret", "@test", "caption", "https://example.org/cover.webp"),
                ("sent", 100),
            )
        self.assertEqual(post.call_count, 2)
        self.assertTrue(post.call_args.args[0].endswith("/sendMessage"))

    def test_ambiguous_photo_is_not_retried_as_text(self):
        import requests

        with patch(
            "reading_telegram.requests.post", side_effect=requests.Timeout()
        ) as post:
            self.assertEqual(
                send("secret", "@test", "caption", "https://example.org/cover.webp"),
                ("uncertain", None),
            )
        self.assertEqual(post.call_count, 1)

    def test_rate_limit_wait_is_persisted(self):
        with (
            patch(
                "reading_telegram.requests.post",
                return_value=Mock(
                    status_code=429,
                    json=lambda: {"ok": False, "parameters": {"retry_after": 60}},
                ),
            ),
            patch("reading_telegram.time.time", return_value=1000),
        ):
            self.assertEqual(send("secret", "@test", "caption"), ("retry:1060", None))

    def test_rate_limited_job_waits_and_then_retries(self):
        catalog = self.catalog()
        catalog["channels"] = catalog["channels"][:1]
        sender = Mock(side_effect=[("retry:1060", None), ("sent", 50)])
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram.time.sleep"),
            patch("reading_telegram.time.time", return_value=1000),
        ):
            run(catalog, date(2026, 11, 1), self.root / "retry.db", True, sender=sender)
            result = run(
                catalog, date(2026, 11, 1), self.root / "retry.db", True, sender=sender
            )
            self.assertEqual(sender.call_count, 1)
            self.assertEqual(result[0]["status"], "skipped:retry:1060")
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram.time.sleep"),
            patch("reading_telegram.time.time", return_value=1061),
        ):
            result = run(
                catalog, date(2026, 11, 1), self.root / "retry.db", True, sender=sender
            )
        self.assertEqual(result[0]["status"], "sent")
        self.assertEqual(sender.call_count, 2)

    def test_labelled_smoke_preview(self):
        result = smoke(self.catalog(), "8498382378", self.root / "smoke.db")
        self.assertIn("PRUEBA", result[0]["text"])
        self.assertNotIn("Novedad de hoy", result[0]["text"])
        self.assertIn("1 de noviembre de 2026", result[0]["text"])
        self.assertFalse((self.root / "smoke.db").exists())

    def test_smoke_delivery_and_dedup(self):
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram.time.sleep"),
        ):
            sender = Mock(return_value=("sent", 5))
            db = self.root / "smoke.db"
            result = smoke(self.catalog(), "8498382378", db, True, sender=sender)
            self.assertEqual(result[0]["status"], "sent")
            self.assertIn("PRUEBA", sender.call_args.args[2])
            smoke(self.catalog(), "8498382378", db, True, sender=sender)
            self.assertEqual(sender.call_count, 2)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = {
            "categorias": [{"id": "fantasia", "nombre": "Fantasía", "tipo": "genero"}],
            "libro_categorias": [{"libro_id": "one", "categoria_id": "fantasia"}],
            "libros": [
                {
                    "id": "one",
                    "estado": "publicado",
                    "titulo": "Libro <uno>",
                    "autores": ["Autora"],
                    "fecha_publicacion": "2026-11-01",
                    "fuente_publicacion_url": "https://editorial.example/libro",
                    "url_amazon_afiliada": "https://www.amazon.es/dp/8498382378?tag=davidporto-21",
                }
            ],
        }
        self.config = {
            "enabled": True,
            "demo": False,
            "channels": [
                {"chat_id": "@general", "token_env": "TEST_TOKEN", "categories": []},
                {
                    "chat_id": "@fantasia",
                    "token_env": "TEST_TOKEN",
                    "categories": ["fantasia"],
                },
            ],
        }

    def catalog(self):
        for name, data in [
            ("catalog.json", self.source),
            ("channels.json", self.config),
        ]:
            (self.root / name).write_text(json.dumps(data), encoding="utf-8")
        return from_reading_catalogue(
            self.root / "catalog.json", self.root / "channels.json"
        )

    def test_native_links_categories_and_preview(self):
        catalog = self.catalog()
        db = self.root / "state.db"
        result = run(catalog, date(2026, 11, 1), db)
        self.assertEqual(len(result), 2)
        self.assertIn("tag=davidporto-21", result[0]["text"])
        self.assertIn("&lt;uno&gt;", result[0]["text"])
        self.assertIn("Fantasía", result[0]["text"])
        self.assertNotIn("comisión", result[0]["text"])
        self.assertEqual(run(catalog, date(2026, 11, 2), db), [])
        self.assertFalse(db.exists())

    def test_digest_channel_gets_one_daily_message_with_isbn_filter(self):
        second = {
            **self.source["libros"][0],
            "id": "two",
            "titulo": "Libro dos",
            "isbn13": "9788401042751",
            "url_amazon_afiliada": "https://www.amazon.es/dp/8401042755?tag=davidporto-21",
        }
        self.source["libros"][0]["isbn13"] = "9788498382372"
        self.source["libros"].append(second)
        self.config["channels"].append(
            {"chat_id": "@novedades", "token_env": "TEST_TOKEN", "mode": "digest"}
        )
        result = run(self.catalog(), date(2026, 11, 1), self.root / "state.db")
        digests = [r for r in result if r["chat_id"] == "@novedades"]
        self.assertEqual(len(digests), 1)
        text = digests[0]["text"]
        self.assertIn("Aquí tienes las publicaciones del día 1 de noviembre", text)
        self.assertIn("2 libros", text)
        self.assertIn("#publicidad", text)
        self.assertIn("rh=p_66:9788498382372|9788401042751", text)
        self.assertIn("tag=davidporto-21", text)
        self.assertIn("&lt;uno&gt;", text)
        self.assertEqual(len([r for r in result if r["chat_id"] == "@general"]), 2)
        self.assertEqual(run(self.catalog(), date(2026, 11, 2), self.root / "s.db"), [])

    def test_discord_channel_posts_digest_by_webhook_without_bot_token(self):
        self.source["libros"][0]["isbn13"] = "9788498382372"
        hook = "https://discord.com/api/webhooks/123/abc_DEF-9"
        self.config["channels"] = [
            {"platform": "discord", "chat_id": "discord-avisos", "webhook": hook, "mode": "digest"}
        ]
        discord = Mock(return_value=("sent", 1234567890123456789))
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("reading_telegram.time.sleep"),
        ):
            result = run(self.catalog(), date(2026, 11, 1), self.root / "d.db", True,
                         sender=Mock(side_effect=AssertionError("telegram")),
                         discord_sender=discord)
        self.assertEqual(result[0]["status"], "sent")
        self.assertEqual(discord.call_args.args[0], hook)
        self.assertNotIn(hook, json.dumps(result))

    def test_discord_text_is_markdown_and_split_in_2000_char_parts(self):
        from reading_telegram import discord_parts
        html = "📚 <b>Novedades de hoy (2)</b>\n\n" + "\n".join(
            f"• <b>T&amp;{i}</b> — A" + "x" * 300 for i in range(12)
        ) + '\n\n<a href="https://www.amazon.es/s?i=stripbooks&amp;rh=p_66%3A1">Ver todas en Amazon</a>'
        parts = discord_parts(html)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(p) <= 2000 for p in parts))
        self.assertTrue(parts[0].startswith("📚 **Novedades de hoy (2)**"))
        joined = "\n".join(parts)
        for i in range(12):
            self.assertIn(f"**T&{i}**", joined)  # nothing is dropped, only split
        self.assertTrue(parts[-1].endswith("[Ver todas en Amazon](<https://www.amazon.es/s?i=stripbooks&rh=p_66%3A1>)"))

    def test_edition_note_describes_book_without_synopsis(self):
        from reading_telegram import edition_note
        book = {"titulo": "La madre", "autores": ["José María Zavala"],
                "descripcion_breve": "La madre, de José María Zavala. Edición de Ediciones B en castellano, "
                "en tapa dura. Consta de 536 páginas. Publicación editorial: 2026-11-10."}
        self.assertEqual(edition_note(book), "Edición de Ediciones B en castellano, en tapa dura. Consta de 536 páginas.")
        self.assertEqual(edition_note({"titulo": "X", "autores": []}), "")

    def test_discord_channel_requires_a_real_webhook(self):
        self.config["channels"] = [
            {"platform": "discord", "chat_id": "discord-avisos", "webhook": "https://example.com/x"}
        ]
        with self.assertRaises(ValueError):
            self.catalog()

    def test_digest_is_sent_once_per_day(self):
        self.source["libros"][0]["isbn13"] = "9788498382372"
        self.config["channels"] = [
            {"chat_id": "@novedades", "token_env": "TEST_TOKEN", "mode": "digest"}
        ]
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram.time.sleep"),
        ):
            sender = Mock(return_value=("sent", 7))
            db = self.root / "digest.db"
            run(self.catalog(), date(2026, 11, 1), db, True, sender=sender)
            again = run(self.catalog(), date(2026, 11, 1), db, True, sender=sender)
        self.assertEqual(sender.call_count, 1)
        self.assertIsNone(sender.call_args.args[3])
        self.assertEqual(again, [{"chat_id": "@novedades", "asin": "digest-2026-11-01", "status": "skipped:sent"}])

    def test_pending_partial_dates_search_links_and_unpublished(self):
        for field, value in [
            ("fecha_publicacion", "2026-11"),
            ("estado", "borrador"),
            ("url_amazon_afiliada", "https://www.amazon.es/s?k=isbn"),
            ("url_amazon_afiliada", "https://www.amazon.es.evil/dp/8498382378"),
            ("fuente_publicacion_url", ""),
        ]:
            with self.subTest(field=field, value=value):
                old = copy.deepcopy(self.source)
                self.source["libros"][0][field] = value
                self.assertEqual(self.catalog()["books"], [])
                self.source = old

    def test_disabled_configuration(self):
        self.config["enabled"] = False
        with self.assertRaises(ValueError):
            self.catalog()

    def test_demo_blocks_send(self):
        self.config["demo"] = True
        with self.assertRaises(ValueError):
            run(self.catalog(), date(2026, 11, 1), self.root / "db", True)

    def test_restart_and_uncertain_delivery(self):
        for status in ["sent", "uncertain", "rejected"]:
            with (
                self.subTest(status=status),
                patch.dict("os.environ", {"TEST_TOKEN": "test"}),
                patch("reading_telegram.time.sleep"),
            ):
                sender = Mock(return_value=(status, 42 if status == "sent" else None))
                db = self.root / (status + ".db")
                run(self.catalog(), date(2026, 11, 1), db, True, sender=sender)
                result = run(self.catalog(), date(2026, 11, 1), db, True, sender=sender)
                self.assertEqual(sender.call_count, 2)
                self.assertTrue(all(r["status"] == "skipped:" + status for r in result))

    def test_crash_claim_survives(self):
        with patch.dict("os.environ", {"TEST_TOKEN": "test"}):
            with self.assertRaises(RuntimeError):
                run(
                    self.catalog(),
                    date(2026, 11, 1),
                    self.root / "crash.db",
                    True,
                    sender=Mock(side_effect=RuntimeError()),
                )
            with closing(sqlite3.connect(self.root / "crash.db")) as db:
                self.assertEqual(
                    db.execute("SELECT status FROM deliveries").fetchone()[0], "sending"
                )

    def add_book(self, ident, isbn, day, categories=("fantasia",)):
        self.source["libros"].append({
            **self.source["libros"][0], "id": ident, "titulo": f"Libro {ident}",
            "isbn13": isbn, "fecha_publicacion": day,
            "url_amazon_afiliada": f"https://www.amazon.es/dp/B{isbn[-9:]}?tag=davidporto-21",
        })
        self.source["libro_categorias"] += [{"libro_id": ident, "categoria_id": c} for c in categories]

    def test_nothing_is_sent_before_1130_madrid(self):
        from datetime import datetime
        catalog = self.catalog()
        self.assertEqual(run(catalog, date(2026, 11, 1), self.root / "a.db",
                             now=datetime(2026, 11, 1, 11, 29)), [])
        self.assertEqual(len(run(catalog, date(2026, 11, 1), self.root / "a.db",
                                 now=datetime(2026, 11, 1, 11, 30))), 2)

    def test_weekly_digest_only_on_monday_covers_next_seven_days(self):
        self.source["libros"][0]["isbn13"] = "9788498382372"
        self.source["libros"][0]["fecha_publicacion"] = "2026-11-02"
        self.add_book("b", "9788401042751", "2026-11-08")
        self.add_book("c", "9788401042768", "2026-11-09")  # next week: not repeated
        self.config["channels"] = [
            {"chat_id": "@proximos", "token_env": "TEST_TOKEN", "mode": "digest", "period": "weekly"}
        ]
        catalog = self.catalog()
        self.assertEqual(run(catalog, date(2026, 11, 3), self.root / "w.db"), [])
        result = run(catalog, date(2026, 11, 2), self.root / "w.db")
        self.assertEqual(len(result), 1)
        text = result[0]["text"]
        self.assertIn("Próximos lanzamientos del 2 de noviembre al 8 de noviembre", text)
        self.assertIn("8 de noviembre: <b>Libro b</b>", text)
        self.assertIn("9788498382372|9788401042751", text)
        self.assertNotIn("9788401042768", text)
        next_week = run(catalog, date(2026, 11, 9), self.root / "w.db")
        self.assertIn("9788401042768", next_week[0]["text"])
        self.assertNotIn("9788401042751", next_week[0]["text"])

    def test_weekly_channel_must_be_a_digest(self):
        self.config["channels"] = [{"chat_id": "@x", "token_env": "T", "period": "weekly"}]
        with self.assertRaises(ValueError):
            self.catalog()

    def test_group_gives_categories_and_label(self):
        self.source["libros"][0]["isbn13"] = "9788498382372"
        self.add_book("terror", "9788401042751", "2026-11-01", categories=())
        self.config["channels"] = [
            {"chat_id": "@fan", "token_env": "T", "group": "fantasia", "mode": "digest"}
        ]
        for name, data in [("catalog.json", self.source), ("channels.json", self.config)]:
            (self.root / name).write_text(json.dumps(data), encoding="utf-8")
        groups = {"fantasia": {"name": "Fantasía", "categories": ["fantasia"]}}
        catalog = from_reading_catalogue(self.root / "catalog.json", self.root / "channels.json", groups)
        text = run(catalog, date(2026, 11, 1), self.root / "g.db")[0]["text"]
        self.assertIn("Fantasía · 1 libro", text)
        self.assertNotIn("Libro terror", text)
        with self.assertRaises(ValueError):
            from_reading_catalogue(self.root / "catalog.json", self.root / "channels.json", {})

    def test_large_day_is_batched_paced_and_interleaved(self):
        for n in range(30):
            self.add_book(f"n{n}", f"97884010{n:05d}", "2026-11-01")
        self.config["channels"].append(
            {"chat_id": "@resumen", "token_env": "TEST_TOKEN", "mode": "digest"}
        )
        checkpoints, order = [], []
        sender = Mock(side_effect=lambda t, chat, text, photo=None: (order.append(chat), ("sent", 1))[1])
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram.time.sleep"),
        ):
            result = run(self.catalog(), date(2026, 11, 1), self.root / "big.db", True,
                         sender=sender, checkpoint=checkpoints.append)
        self.assertEqual(len(result), 63)
        self.assertTrue(all(r["status"] == "sent" for r in result))
        self.assertEqual(order[0], "@resumen")  # the digest goes first
        self.assertEqual(order[1:3], ["@general", "@fantasia"])  # then round robin
        self.assertLessEqual(len(checkpoints), 2 * (63 // 25 + 1))  # per batch, not per message

    def test_rate_limit_releases_rest_of_channel_for_next_cycle(self):
        for n in range(3):
            self.add_book(f"n{n}", f"97884010{n:05d}", "2026-11-01")
        self.config["channels"] = self.config["channels"][:1]
        sender = Mock(side_effect=[("sent", 1), ("retry:99999999999", None)])
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram.time.sleep"),
        ):
            result = run(self.catalog(), date(2026, 11, 1), self.root / "rl.db", True, sender=sender)
            self.assertEqual([r["status"][:5] for r in result], ["sent", "retry"])
            sender.side_effect = None
            sender.return_value = ("sent", 2)
            again = run(self.catalog(), date(2026, 11, 1), self.root / "rl.db", True, sender=sender)
        self.assertEqual(sorted(r["status"][:7] for r in again),
                         ["sent", "sent", "skipped", "skipped"])

    def test_cover_resolver_replaces_generated_cover(self):
        self.config["channels"] = self.config["channels"][:1]
        sender = Mock(return_value=("sent", 1))
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram.time.sleep"),
        ):
            run(self.catalog(), date(2026, 11, 1), self.root / "cv.db", True, sender=sender,
                cover_resolver=lambda book: "https://m.media-amazon.com/images/I/real.jpg")
        self.assertEqual(sender.call_args.args[3], "https://m.media-amazon.com/images/I/real.jpg")

    def test_discord_long_digest_goes_in_parts_and_partial_failure_is_uncertain(self):
        from reading_telegram import send_discord
        hook = "https://discord.com/api/webhooks/123/abc"
        text = "\n".join("• <b>Título</b> — " + "x" * 300 for _ in range(12))
        ok = Mock(status_code=200, json=lambda: {"id": "11"})
        with patch("reading_telegram.requests.post", side_effect=[ok] * 5) as post,                 patch("reading_telegram.time.sleep"):
            self.assertEqual(send_discord(hook, "d", text), ("sent", 11))
        self.assertGreater(post.call_count, 1)
        bad = Mock(status_code=500, json=lambda: {})
        with patch("reading_telegram.requests.post", side_effect=[ok, bad]),                 patch("reading_telegram.time.sleep"), patch("builtins.print"):
            self.assertEqual(send_discord(hook, "d", text), ("uncertain", 11))

    def test_transport_validates_response_and_redacts_errors(self):
        with patch(
            "reading_telegram.requests.post",
            return_value=Mock(
                status_code=200, json=lambda: {"ok": True, "result": {"message_id": 7}}
            ),
        ):
            self.assertEqual(send("secret", "@test", "text"), ("sent", 7))
        with patch(
            "reading_telegram.requests.post",
            return_value=Mock(status_code=200, json=lambda: {"ok": True}),
        ):
            self.assertEqual(send("secret", "@test", "text"), ("uncertain", None))
        import requests

        with (
            patch(
                "reading_telegram.requests.post", side_effect=requests.Timeout("secret")
            ),
            patch("builtins.print") as output,
        ):
            self.assertEqual(send("secret", "@test", "text"), ("uncertain", None))
            # Only the exception type reaches the log, never its message (it can carry the token URL).
            printed = repr(output.call_args_list)
            self.assertIn("Timeout", printed)
            self.assertNotIn("secret", printed)
        with (
            patch(
                "reading_telegram.requests.post",
                return_value=Mock(
                    status_code=403,
                    json=lambda: {
                        "ok": False,
                        "description": "Forbidden: bot is not a member of the channel chat",
                    },
                ),
            ),
            patch("builtins.print") as output,
        ):
            self.assertEqual(send("secret", "@test", "text"), ("rejected", None))
            printed = repr(output.call_args_list)
            self.assertIn("HTTP 403 Forbidden: bot is not a member", printed)
            self.assertNotIn("secret", printed)
            self.assertNotIn("@test", printed)


if __name__ == "__main__":
    unittest.main()
