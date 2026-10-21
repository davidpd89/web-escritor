"""Export CSV -> approved-only JSON with precise real book identity (offline)."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reading_review_export", ROOT / "scripts/export-reading-approved-reviews.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BOOKS = [
    {"id": "lib-0001", "isbn13": "9788498382372", "estado": "publicado"},
    {"id": "isbn-9788425371967", "isbn13": "9788425371967", "estado": "publicado"},
    {"id": "pending", "isbn13": "9788401036897", "estado": "borrador"},
]


def row(review_id, *, state="aprobada", consent="si", stars="5", book_id="lib-0001",
        isbn="9788498382372"):
    return {
        "resena_id": review_id, "libro_id": book_id, "isbn13": isbn,
        "nombre_publico": "Lector/a", "puntuacion_1a5": stars,
        "titulo_resena": "Buen libro", "texto_resena": "Reseña de prueba con contenido verificable.",
        "fecha_envio": "2026-10-21", "estado_moderacion": state,
        "consentimiento_publicacion": consent,
        "nota_interna": "CONFIDENCIAL NO PUBLICAR", "origen": "formulario",
    }


class ReviewModerationTest(unittest.TestCase):
    def test_only_approved_and_consented_public_with_no_internal_fields(self):
        records = [
            row("r1"), row("r2", state="pendiente"), row("r3", state="rechazada"),
            row("r4", consent="no"), row("r5", book_id="LIB-0001"),
        ]
        result = mod.approved_rows(records, BOOKS)
        self.assertEqual([r["review_id"] for r in result], ["r1", "r5"])
        self.assertTrue(all(r["libro_id"] == "lib-0001" for r in result))
        serial = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("CONFIDENCIAL", serial)
        self.assertNotIn("nota_interna", serial)
        self.assertNotIn("r2", serial)
        self.assertNotIn("r3", serial)
        self.assertNotIn("r4", serial)

    def test_cannot_misattribute_review_to_a_different_isbn(self):
        with self.assertRaisesRegex(ValueError, "no coinciden"):
            mod.approved_rows([row("bad", book_id="lib-0001", isbn="9788425371967")], BOOKS)
        with self.assertRaisesRegex(ValueError, "ISBN sin libro"):
            mod.approved_rows([row("bad", book_id="legacy", isbn="9780000000000")], BOOKS)

    def test_invalid_rating_duplicate_and_missing_identity_are_rejected(self):
        for bad in (row("r", stars="0"), row("r", stars="6"), row("r", stars="abc")):
            with self.assertRaises(ValueError):
                mod.approved_rows([bad], BOOKS)
        with self.assertRaises(ValueError):
            mod.approved_rows([row("r"), row("r")], BOOKS)
        with self.assertRaises(ValueError):
            mod.approved_rows([row("")], BOOKS)

    def test_moderation_reversal_retracts_review(self):
        records = [row("r1")]
        self.assertEqual(len(mod.approved_rows(records, BOOKS)), 1)
        records[0]["estado_moderacion"] = "rechazada"
        self.assertEqual(mod.approved_rows(records, BOOKS), [])

    def test_pending_and_rejected_never_raise_on_malformed_content(self):
        records = [row("r1", state="pendiente", stars="garbage"),
                   row("r2", state="rechazada", isbn="garbage")]
        self.assertEqual(mod.approved_rows(records, BOOKS), [])


if __name__ == "__main__":
    unittest.main()
