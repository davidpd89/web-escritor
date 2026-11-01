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
from reading_telegram import from_reading_catalogue, run, send, smoke


class ReadingTelegramTests(unittest.TestCase):
    def test_labelled_smoke_preview(self):
        result = smoke(self.catalog(), "8498382378", self.root / "smoke.db")
        self.assertIn("PRUEBA", result[0]["text"])
        self.assertNotIn("Novedad de hoy", result[0]["text"])
        self.assertIn("2026-11-01", result[0]["text"])
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
            output.assert_not_called()


if __name__ == "__main__":
    unittest.main()
