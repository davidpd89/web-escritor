"""Synthetic tests for atlas offline identity candidate proposals.

No network, real data, automatic merges, publication or CI runs.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

F = Path(__file__).resolve().parents[1] / "scripts/atlas_candidate_identity_proposals.py"
spec = importlib.util.spec_from_file_location("atlas_match_proposals", F)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def place(rid="pla-a", name="Biblioteca Álamos", qid=None, lat=40.4167, lon=-3.7033):
    row = {"id": rid, "status": "candidate", "name": name,
           "destination_id": "dst-madrid", "geo_precision": "point",
           "latitude": lat, "longitude": lon}
    if qid:
        row["wikidata_qid"] = qid
    return row


class IdentityProposalsTests(unittest.TestCase):
    def test_same_qid_is_review_only_not_auto_merged(self):
        a = place(qid="Q123")
        b = place("pla-b", "Nombre totalmente distinto", "Q123", 40.8, -3.2)
        out = mod.propose([a], [b])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["reason"], "shared_external_id_review")
        self.assertEqual(out[0]["shared_keys"], ["wikidata_qid:Q123"])
        self.assertFalse(out[0]["automatic_merge"])

    def test_nearby_same_name_without_shared_id_only_proposes(self):
        a = place()
        b = place("pla-b", "Biblioteca Alamos", lat=40.4168, lon=-3.7034)
        out = mod.propose([a], [b])
        self.assertEqual(out[0]["reason"], "same_name_nearby_review")
        self.assertLess(out[0]["distance_m"], 150)

    def test_distant_same_named_franchises_do_not_match(self):
        self.assertEqual(mod.propose([place()], [place("pla-b", lat=41.0, lon=-3.7)]), [])

    def test_city_centroid_never_used_to_claim_same_building(self):
        a = place()
        b = place("pla-b")
        b["geo_precision"] = "city"
        self.assertEqual(mod.propose([a], [b]), [])

    def test_different_qids_nearby_are_flagged_conflict(self):
        a = place(qid="Q123")
        b = place("pla-b", "Biblioteca Álamos", "Q456",
                  lat=40.4168, lon=-3.7034)
        out = mod.propose([a], [b])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["reason"], "conflicting_qids_review")

    def test_shared_qid_across_destinations_flags_conflict(self):
        a = place(qid="Q123")
        b = place("pla-b", qid="Q123")
        b["destination_id"] = "dst-other"
        out = mod.propose([a], [b])
        self.assertEqual(out[0]["reason"], "same_id_different_destination_review")

    def test_unapproved_input_or_duplicate_ids_fail_closed(self):
        a = place()
        a["status"] = "approved"
        with self.assertRaises(ValueError):
            mod.propose([a], [place("pla-b")])
        with self.assertRaises(ValueError):
            mod.propose([place()], [place()])

    def test_alias_normalization_does_not_merge_without_geography(self):
        a = place()
        b = place("pla-b", name="Biblioteca Alamos")
        b.pop("latitude")
        b.pop("longitude")
        self.assertEqual(mod.propose([a], [b]), [])

    def test_osm_type_id_is_not_confused(self):
        a, b = place(), place("pla-b", "Otro nombre")
        a.update(osm_type="node", osm_id="12345")
        b.update(osm_type="way", osm_id="12345")
        self.assertEqual(mod.propose([a], [b]), [])
        b["osm_type"] = "node"
        self.assertEqual(mod.propose([a], [b])[0]["reason"],
                         "shared_external_id_review")


if __name__ == "__main__":
    unittest.main()
