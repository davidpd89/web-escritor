"""Pruebas offline de los auxiliares para ingesta: ningún HTTP ni API ni LLM."""
import importlib.util
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reading_intake_core", ROOT / "scripts/reading_intake_core.py"
)
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)

CONFIG = json.loads(
    (ROOT / "data/reading-intake-sources.example.json").read_text(encoding="utf-8")
)


class IntakeCoreTests(unittest.TestCase):
    def test_isbn_checksum_conversion_and_invalid(self):
        self.assertEqual(core.isbn13("978-84-9838-237-2"), "9788498382372")
        self.assertEqual(core.isbn13("8498382378"), "9788498382372")
        self.assertIsNone(core.isbn13("9788498382373"))
        self.assertIsNone(core.isbn13("not-an-isbn"))
        self.assertEqual(core.isbn13("9791300000005"), "9791300000005")  # bloque español 979-13

    def test_date_precision_and_invalid_dates(self):
        self.assertEqual(core.edition_date("2026"), ("2026", "anio"))
        self.assertEqual(core.edition_date("2026-10"), ("2026-10", "mes"))
        self.assertEqual(core.edition_date("2026-10-20"), ("2026-10-20", "dia"))
        self.assertEqual(core.edition_date("2026-02-29"), (None, "desconocida"))
        self.assertEqual(core.edition_date("2026-13"), (None, "desconocida"))

    def test_novelty_windows_utc_independent(self):
        today = date(2026, 10, 20)
        self.assertEqual(core.novelty_labels("2026-10-01", today),
                         ("ultimos-30", "ultimos-90"))
        self.assertEqual(core.novelty_labels("2026-08-25", today), ("ultimos-90",))
        self.assertEqual(core.novelty_labels("2026-11-03", today), ("proximos-30",))
        self.assertEqual(core.novelty_labels("2026-10", today), ())
        self.assertEqual(core.novelty_labels("2009-06-01", today), ())

    def test_publisher_allowlist_exact_alias(self):
        publishers = CONFIG["publishers"]
        self.assertEqual(core.publisher_slug("Salamandra Infantil y Juvenil", publishers), "salamandra")
        self.assertEqual(core.publisher_slug("NOCTURNA EDICIONES", publishers), "nocturna-ediciones")
        self.assertIsNone(core.publisher_slug("Independently published", publishers))
        self.assertIsNone(core.publisher_slug("Salamandra de autores independientes", publishers))
        self.assertEqual(core.publisher_slug("Nova", publishers), "nova")

    def test_affiliate_search_is_not_product(self):
        item = core.affiliate_destination("9788498382372", "davidporto-21")
        self.assertEqual(item["tipo"], "busqueda_isbn")
        self.assertIn("k=9788498382372", item["url"])
        self.assertIn("tag=davidporto-21", item["url"])
        self.assertIn("Buscar", item["texto"])

    def test_direct_amazon_product_requires_confirmed_asin(self):
        item = core.affiliate_destination("9788498382372", "davidporto-21", "8498382378")
        self.assertEqual(item["tipo"], "producto_verificado")
        self.assertEqual(item["url"],
                         "https://www.amazon.es/dp/8498382378?tag=davidporto-21")
        with self.assertRaises(ValueError):
            core.affiliate_destination("9788498382372", "bad tag!", "8498382378")
        with self.assertRaises(ValueError):
            core.affiliate_destination("9788498382372", "davidporto-21", "INVALID_ASIN")

    def test_google_search_params_and_api_limits(self):
        data = core.google_books_query("Salamandra", "test-key", page=1)
        self.assertEqual(data["q"], "inpublisher:Salamandra")
        self.assertEqual(data["startIndex"], 40)
        self.assertEqual(data["maxResults"], 40)
        self.assertEqual(data["showPreorders"], "true")
        with self.assertRaises(ValueError):
            core.google_books_query("Salamandra", "test-key", max_results=41)

    def test_google_candidate_only_if_confident(self):
        vol = {"id": "google-id", "volumeInfo": {
            "title": "Ejemplo", "authors": ["Persona de prueba"],
            "publisher": "Salamandra", "language": "es",
            "publishedDate": "2026-10",
            "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9788498382372"}],
        }}
        item = core.google_books_candidate(vol, CONFIG["publishers"])
        self.assertEqual(item["candidate_key"], "isbn13:9788498382372")
        self.assertEqual(item["precision_fecha"], "mes")
        self.assertEqual(item["editorial_sello_slug"], "salamandra")
        # "OTHER" is never used as ISBN if no explicit ISBN entry exists.
        vol["volumeInfo"]["industryIdentifiers"] = [{"type": "OTHER", "identifier": "9788498382372"}]
        self.assertIsNone(core.google_books_candidate(vol, CONFIG["publishers"]))
        vol["volumeInfo"]["publisher"] = "Independently published"
        self.assertIsNone(core.google_books_candidate(vol, CONFIG["publishers"]))


if __name__ == "__main__":
    unittest.main()
