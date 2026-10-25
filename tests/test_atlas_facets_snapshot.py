"""Synthetic isolated tests for country manifest and per-destination facet shards."""
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("atlas_facets_snapshot", SCRIPTS / "atlas_facets_snapshot.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

DESC = "Texto original sobre un destino con referencias, visitas y obras literarias. " * 3


def fixture():
    return {
        "destinations": [{"id": "dst-demo", "slug": "demo-ciudad",
                          "name": "Ciudad imaginaria", "country_iso2": "ES",
                          "status": "approved", "verified_at": "2026-10-21",
                          "summary_original": DESC}],
        "places": [{"id": "pla-demo", "slug": "libreria-de-ejemplo",
                    "name": "Librería de ejemplo", "place_type": "bookshop",
                    "status": "approved", "verified_at": "2026-10-21",
                    "destination_id": "dst-demo", "summary_original": DESC,
                    "source_ids": ["src-demo"]}],
        "sources": [{"id": "src-demo", "title": "Fuente sintética", "url": "https://example.org/source",
                     "evidence_summary": "Ficción sintética", "retrieved_at": "2026-10-21"}],
        "works": [{"id": "wrk-demo", "title": "Libro sintético",
                   "status": "approved", "verified_at": "2026-10-21"}],
        "authors": [], "adaptations": [],
        "relationships": [{"id": "rel-demo", "place_id": "pla-demo",
                           "status": "approved", "verified_at": "2026-10-21",
                           "subject_type": "work", "subject_id": "wrk-demo",
                           "relationship_type": "narrative_explicit",
                           "evidence_note": "Cita sintética", "source_ids": ["src-demo"]}],
    }


class FacetShardsTest(unittest.TestCase):
    def test_manifest_and_one_shard(self):
        manifest, shards = mod.facet_shards(fixture())
        self.assertEqual([x["iso2"] for x in manifest["countries"]], ["ES"])
        self.assertEqual(manifest["countries"][0]["destinations"][0]["count"], 1)
        self.assertEqual(shards["demo-ciudad"]["places"][0]["type"], "bookshop")
        self.assertEqual(shards["demo-ciudad"]["places"][0]["relations"][0]["subject_name"],
                         "Libro sintético")

    def test_unapproved_relationship_not_in_filters(self):
        data = fixture()
        data["relationships"][0]["status"] = "candidate"
        _, shards = mod.facet_shards(data)
        self.assertEqual(shards["demo-ciudad"]["places"][0]["relations"], [])

    def test_unapproved_place_does_not_make_facet_pages(self):
        data = fixture()
        data["places"][0]["status"] = "candidate"
        manifest, shards = mod.facet_shards(data)
        self.assertEqual(shards, {})
        self.assertEqual(manifest["countries"], [])

    def test_invalid_country_iso_does_not_create_file_path(self):
        data = fixture()
        data["destinations"][0]["country_iso2"] = "XX/../"
        with self.assertRaisesRegex(ValueError, "ISO2"):
            mod.facet_shards(data)

    def test_filming_on_work_is_not_public_facet(self):
        data = fixture()
        data["relationships"][0]["relationship_type"] = "filming_location"
        _, shards = mod.facet_shards(data)
        self.assertEqual(shards["demo-ciudad"]["places"][0]["relations"], [])

    def test_bad_https_source_never_makes_a_public_facet(self):
        data = fixture()
        data["sources"][0]["url"] = "https://"
        manifest, shards = mod.facet_shards(data)
        self.assertEqual(manifest["countries"], [])
        self.assertEqual(shards, {})



if __name__ == "__main__":
    unittest.main()
