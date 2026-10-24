"""Offline regression cases for publisher reconciliation.

No network, no write to public data, no import of Actions/publishing modules.
"""
import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/gpt_editoriales_reconcile.py"
spec = importlib.util.spec_from_file_location("gpt_editoriales_reconcile", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

TODAY = date(2026, 10, 22)
URL = "https://www.penguinlibros.com/es/libro-de-fantasia/123-libro-ejemplo-9788400000000"


def record(slug, name, status="unknown", checked="2026-10-21", email=None):
    return {
        "slug": slug, "name": name, "status": status,
        "verified_at": checked, "submission_email": email,
        "sources": [{"primary": True, "url": "https://editorial-ejemplo.es/contacto"}],
    }


def imprint(slug, name, sources=None):
    return {
        "slug": slug, "nombre": name, "grupo": "Grupo inventado",
        "fecha_verificacion": "2026-10-21",
        "fuentes": [{"url": s, "titulo": "Ficha de la edición"} for s in (sources if sources is not None else [URL])],
    }


def book(ident, directory=None, catalogue=None, state="publicado"):
    return {"id": ident, "estado": state, "editorial_slug": directory,
            "editorial_catalogo_slug": catalogue}


def report(manual=None, seals=None, books=None, *, as_of=TODAY):
    return module.reconcile(
        {"publishers": manual if manual is not None else []},
        {"editoriales": seals if seals is not None else []},
        {"libros": books if books is not None else []},
        as_of=as_of,
    )


class PublisherReconciliationTests(unittest.TestCase):
    def test_duplicate_books_cannot_inflate_publisher_support(self):
        with self.assertRaisesRegex(ValueError, "Duplicate book ID"):
            report(books=[book("same", catalogue="sello"), book("same", catalogue="sello")])

    def test_closed_publisher_can_keep_publishing_books(self):
        data = report(manual=[record("editorial-sol", "Editorial Sol", status="closed",
                                     email="manuscritos@editorial-ejemplo.es")],
                      books=[book("isbn-a", directory="editorial-sol")])
        self.assertEqual(data["linked_book_status_counts"], {"closed": 1})
        self.assertEqual(data["counts"]["directory_submission_email_records"], 1)
        self.assertNotIn("manuscritos@editorial-ejemplo.es", json.dumps(data))
        self.assertFalse(data["publish_changes"])

    def test_alias_only_suggests_review_without_merging(self):
        data = report(manual=[record("ediciones-sol", "Ediciones Sol")],
                      seals=[imprint("sol", "Sol")],
                      books=[book("isbn-a", catalogue="sol")])
        item, = data["imprint_candidates"]
        self.assertEqual(item["decision"], "review_alias")
        self.assertEqual(item["possible_directory_slugs"], ["ediciones-sol"])
        self.assertEqual(item["manuscript_status"], "not_inferred")
        self.assertEqual(data["counts"]["linked_to_catalogue_imprint"], 1)

    def test_exact_name_never_auto_merges(self):
        data = report(manual=[record("ediciones-sol", "Ediciones Sol")],
                      seals=[imprint("sello-sol", "Ediciones Sol")])
        self.assertEqual(data["imprint_candidates"][0]["decision"], "review_exact_name")

    def test_slug_collision_takes_precedence_over_similar_name(self):
        data = report(manual=[record("sol", "Ediciones Sol")],
                      seals=[imprint("sol", "Otra persona jurídica")])
        self.assertEqual(data["imprint_candidates"][0]["decision"], "review_slug_collision")

    def test_orphan_imprint_and_unpublished_book(self):
        data = report(seals=[imprint("isla", "Isla")],
                      books=[book("isbn-draft", catalogue="isla", state="pendiente")])
        self.assertTrue(data["imprint_candidates"][0]["orphan"])
        self.assertEqual(data["counts"]["published_books"], 0)
        self.assertEqual(data["counts"]["imprints_without_published_books"], 1)

    def test_foreign_provenance_cannot_pass_for_official_penguin(self):
        data = report(seals=[imprint("other", "Another",
                                   sources=["https://www.penguinlibros.com.evil.example.es/es/book"])])
        self.assertEqual(data["imprint_candidates"][0]["decision"], "quarantine_source")
        self.assertFalse(data["imprint_candidates"][0]["bibliographic_source_valid"])

    def test_missing_and_double_book_links_are_reported(self):
        data = report(books=[
            book("a", directory="missing"),
            book("b", catalogue="not-found"),
            book("c", directory="known", catalogue="imprint"),
            book("d"),
        ])
        self.assertEqual({e["problem"] for e in data["integrity_errors"]}, {
            "missing_directory_slug", "missing_catalogue_slug",
            "two_publisher_targets", "no_publisher_reference",
        })

    def test_invalid_stale_and_recent_checks(self):
        data = report(manual=[
            record("old", "Antigua", checked="2026-06-01"),
            record("future", "Futura", checked="2026-12-31"),
            record("valid", "Reciente", checked="2026-10-21"),
            record("invalid", "Incorrecta", checked="ayer"),
        ])
        self.assertEqual(data["stale_directory_slugs"], ["old"])
        self.assertEqual(data["invalid_verification_slugs"], ["future", "invalid"])
        self.assertEqual(data["counts"]["directory_verification_old"], 1)

    def test_no_directory_name_key_collision_silently_approved(self):
        data = report(manual=[
            record("e-sol", "Editorial Sol"),
            record("another-e-sol", "Editorial-Sol"),
        ])
        self.assertEqual(data["duplicate_normalized_directory_names"]["editorial sol"],
                         ["another-e-sol", "e-sol"])

    def test_https_sources_and_no_username(self):
        self.assertTrue(module.valid_source(URL, permitted_host="www.penguinlibros.com"))
        for fake in ["http://www.penguinlibros.com/a", "https://user@www.penguinlibros.com/",
                     "https://www.penguinlibros.com:8443/",
                     "https://www.penguinlibros.com.evil.es/", "javascript:alert(1)",
                     "https://www.penguinlibros.com/path#fragment"]:
            with self.subTest(fake=fake):
                self.assertFalse(module.valid_source(fake, permitted_host="www.penguinlibros.com"))

    def test_no_hidden_fallback_if_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            missing = folder / "missing.json"
            ret = module.main(["--directory", str(missing),
                               "--catalogue-publishers", str(missing),
                               "--books", str(missing), "--as-of", TODAY.isoformat()])
            self.assertEqual(ret, 2)


if __name__ == "__main__":
    unittest.main()
