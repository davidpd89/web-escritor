"""Synthetic, offline checks for classical gazetteer candidate normalization.

No download, tests not executed, no library or deployment code touched.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts/atlas_pleiades_candidates.py"
spec = importlib.util.spec_from_file_location("atlas_pleiades", PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def example():
    return {
        "type": "FeatureCollection",
        "id": "579885",
        "title": "Athens",
        "review_state": "published",
        "features": [],  # Real record can have empty features.
        "reprPoint": [23.72, 37.97],  # longitude, latitude
        "placeTypes": ["settlement"],
        "names": [
            {"romanized": "Athenae", "attested": "Ἀθῆναι",
             "language": "grc",
             "attestations": [{"timePeriod": "classical"}]},
            {"romanized": "Athenae", "language": "grc"}
        ]
    }


class AncientPlacesTest(unittest.TestCase):
    def test_empty_features_keeps_representative_point_not_exact(self):
        item = mod.place_candidate(example(), release="4.1")
        self.assertEqual(item["status"], "candidate")
        self.assertEqual(item["representative_point"],
                         {"longitude": 23.72, "latitude": 37.97})
        self.assertEqual(item["geo_precision"], "area_or_city")
        self.assertEqual(item["literary_relation_status"], "none")
        self.assertTrue(item["attribution_required"])

    def test_classic_aliaes_and_periods_preserved(self):
        item = mod.place_candidate(example(), release="4.1")
        self.assertEqual(len(item["aliases"]), 2)
        self.assertEqual(item["aliases"][0]["periods"], ["classical"])
        self.assertEqual(item["aliases"][0]["language"], "grc")

    def test_invalid_or_missing_point_not_fake_coordinate(self):
        row = example()
        row["reprPoint"] = [200, 0]
        item = mod.place_candidate(row, release="4.1")
        self.assertIsNone(item["representative_point"])
        self.assertEqual(item["geo_precision"], "unlocated")
        row["reprPoint"] = None
        self.assertIsNone(mod.place_candidate(row, release="4.1")["representative_point"])

    def test_provider_draft_never_becomes_our_approved(self):
        row = example()
        row["review_state"] = "draft"
        self.assertIsNone(mod.place_candidate(row, release="4.1"))

    def test_reject_unidentified_places(self):
        row = example()
        row["id"] = "../bad"
        self.assertIsNone(mod.place_candidate(row, release="4.1"))

    def test_does_not_copy_third_party_bibliographic_html(self):
        row = example()
        row["references"] = [{"formattedCitation": "<div>Protected</div>"}]
        item = mod.place_candidate(row, release="4.1")
        self.assertNotIn("references", item)
        self.assertNotIn("description", item)


if __name__ == "__main__":
    unittest.main()
