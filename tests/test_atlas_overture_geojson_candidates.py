"""Synthetic tests for Overture Places local GeoJSON candidate prefilter.
No network, real download, Actions or production writes.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "scripts/atlas_overture_geojson_candidates.py"
spec = importlib.util.spec_from_file_location("overture_atlas", P)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def feature(typ="book_store", loc=[-3.5, 40.2]):
    return {
        "type": "Feature",
        "id": "3ad30f6e-ff05-43aa-9f0a-e5d52b9e182b",
        "geometry": {"type": "Point", "coordinates": loc},
        "properties": {
            "names": {"primary": "Librería sintética"},
            "taxonomy": {"primary": typ, "hierarchy": ["shopping", typ]},
            "basic_category": typ,
            "confidence": 0.89,
            "phones": ["private-test-number"],
            "emails": ["do-not-export@example.net"],
            "websites": ["https://example.net"],
        }
    }


class OvertureGeoTest(unittest.TestCase):
    def test_bookshop_candidates_only_and_no_pii(self):
        item = mod.candidate(feature(), "2026-09-23.1")
        self.assertEqual(item["kind_candidate"], "bookshop")
        self.assertEqual(item["status"], "candidate")
        self.assertEqual(item["longitude"], -3.5)
        self.assertNotIn("phones", item)
        self.assertNotIn("emails", item)
        self.assertNotIn("websites", item)
        self.assertEqual(item["place_relation_status"], "none")

    def test_taxonomy_v2_categories_without_legacy_field(self):
        for kind, expected in [("library", "library"), ("museum", "museum"),
                               ("historic_site", "historic_site"),
                               ("academic_bookstore", "bookshop"),
                               ("used_bookstore", "bookshop"),
                               ("comic_books_store", "bookshop"),
                               ("memorial_site", "historic_site")]:
            self.assertEqual(mod.candidate(feature(kind), "2026-09-23.1")["kind_candidate"],
                             expected)

    def test_unknown_category_does_not_become_bookplace(self):
        self.assertIsNone(mod.candidate(feature("restaurant"), "2026-09-23.1"))

    def test_invalid_geometry_and_uuid_are_filtered(self):
        self.assertIsNone(mod.candidate(feature(loc=[999, 999]), "2026-09-23.1"))
        f = feature()
        f["id"] = "bad id"
        self.assertIsNone(mod.candidate(f, "2026-09-23.1"))

    def test_duplicate_provider_id_deduplicated(self):
        items = mod.extract({"type": "FeatureCollection", "features": [feature(), feature()]},
                            "2026-09-23.1")
        self.assertEqual(len(items), 1)

    def test_max_candidates_limit(self):
        one = feature()
        two = feature()
        two["id"] = "43e35cf2-2f3b-423c-9990-8fdc3e86c702"
        items = mod.extract({"type": "FeatureCollection", "features": [one, two]},
                            "2026-09-23.1", max_candidates=1)
        self.assertEqual(len(items), 1)


if __name__ == "__main__":
    unittest.main()
