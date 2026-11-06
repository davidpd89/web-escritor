import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("canon", ROOT / "scripts" / "check-canonical-entity-ids.py")
canon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canon)


def page(node):
    return f'<script type="application/ld+json">{json.dumps(node)}</script>'


class ThirdPartyHomonyms(unittest.TestCase):
    def run_on(self, pages):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel, html in pages.items():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text(html, encoding="utf-8")
            old = canon.ROOT
            canon.ROOT = root
            canon.EXPECTED_IDS = {}
            try:
                return canon.main()
            finally:
                canon.ROOT = old

    def test_two_different_books_with_the_same_title_pass(self):
        base = "https://davidportodiaz.com/recomendaciones/libros/"
        self.assertEqual(self.run_on({
            "a/index.html": page({"@type": "Book", "name": "Dinosaurios", "@id": base + "dinosaurios-9791370342654/#book"}),
            "b/index.html": page({"@type": "Book", "name": "Dinosaurios", "@id": base + "dinosaurios-9791370343149/#book"}),
        }), 0)

    def test_own_entity_fragmentation_still_fails(self):
        self.assertEqual(self.run_on({
            "a/index.html": page({"@type": "Book", "name": "Obra", "@id": "https://davidportodiaz.com/#book-obra"}),
            "b/index.html": page({"@type": "Book", "name": "Obra", "@id": "https://davidportodiaz.com/libros/obra/#book"}),
        }), 1)


if __name__ == "__main__":
    unittest.main()
