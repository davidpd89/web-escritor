"""Reconcilia fuentes de novedades con las 150 editoriales que ya existen."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reading_intake_publishers import relevant_publisher, resolve_publishers
from reading_intake_core import publisher_slug


class PublisherRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "data/editoriales.json").read_text(encoding="utf-8"))
        cls.config = json.loads((ROOT / "data/reading-intake-sources.example.json").read_text(encoding="utf-8"))

    def test_real_existing_registry_is_single_source_of_slugs(self):
        self.assertGreaterEqual(len(self.registry["publishers"]), 100)
        chosen = resolve_publishers(self.registry, self.config["publishers"])
        self.assertGreaterEqual(len(chosen), 20)
        slugs = [p["slug"] for p in chosen]
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertIn("editorial-hidra", slugs)
        self.assertIn("salamandra", slugs)
        self.assertIn("puck", slugs)
        self.assertIn("nova", slugs)

    def test_website_publisher_name_and_manual_aliases(self):
        chosen = resolve_publishers(self.registry, self.config["publishers"])
        self.assertEqual(publisher_slug("Salamandra Infantil y Juvenil", chosen), "salamandra")
        self.assertEqual(publisher_slug("Editorial Hidra", chosen), "editorial-hidra")

    def test_not_confuse_manuscript_reception_with_editorial_catalog(self):
        item = {"slug": "prueba", "name": "Editorial ficticia", "publish": True,
                "publisher_type": "tradicional", "genres": ["fantasía"],
                "status": "closed"}
        self.assertTrue(relevant_publisher(item))

    def test_autopublishing_models_are_excluded(self):
        item = {"slug": "prueba", "name": "Servicios ficticios", "publish": True,
                "publisher_type": "editorial y servicios editoriales",
                "genres": ["fantasía"]}
        self.assertFalse(relevant_publisher(item))
        item["publisher_type"] = "tradicional"
        self.assertTrue(relevant_publisher(item))


if __name__ == "__main__":
    unittest.main()
