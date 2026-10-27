import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import json
import reading_intake_core as core  # noqa: E402
from reading_intake_core import clean_title  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "data/reading-intake-sources.example.json").read_text(encoding="utf-8"))


class CleanTitleTests(unittest.TestCase):
    def test_normal_titles_unchanged(self):
        for t in ("Sin piedad (Harry Hole 14)", "¿Quién teme a Virginia Woolf? – Ñandú", "Día 1: «El inicio» · 日本語"):
            self.assertEqual(clean_title(t), t)

    def test_double_spaces_collapsed(self):
        self.assertEqual(clean_title("La señora Dalloway  (edición especial limitada)"),
                         "La señora Dalloway (edición especial limitada)")
        self.assertEqual(clean_title("  A   B \t\n C  "), "A B C")

    def test_unicode_space_runs_collapsed_single_nbsp_kept(self):
        self.assertEqual(clean_title("A   B　　C"), "A B C")
        self.assertEqual(clean_title("Vol. 1"), "Vol. 1")

    def test_idempotent(self):
        for t in ("A  B", "A  B", "ya normal", "  x  "):
            once = clean_title(t)
            self.assertEqual(clean_title(once), once)

    def test_google_books_entry_point_normalizes(self):
        vol = {"id": "g", "volumeInfo": {
            "title": "La señora Dalloway  (edición especial)", "authors": ["Virginia Woolf"],
            "publisher": "Salamandra", "language": "es", "publishedDate": "2026-10",
            "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9788498382372"}]}}
        item = core.google_books_candidate(vol, CONFIG["publishers"])
        self.assertIsNotNone(item)
        self.assertEqual(item["titulo"], "La señora Dalloway (edición especial)")


if __name__ == "__main__":
    unittest.main()
