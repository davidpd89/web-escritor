"""Synthetic acceptance checks for Overture candidate → Atlas v1 fragment.

No API, download, local dataset, production file or Actions.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/atlas_overture_to_contract.py"
spec = importlib.util.spec_from_file_location("overture_convert", SCRIPT)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def row():
    return {
        "id": "ov-1234567890abcdef1234",
        "provider": "overture_places", "status": "candidate",
        "provider_id": "3ad30f6e-ff05-43aa-9f0a-e5d52b9e182b",
        "provider_release": "2026-09-23.1", "provider_confidence": 0.9,
        "kind_candidate": "bookshop", "name": "Librería sintética",
        "longitude": -3.6, "latitude": 40.4
    }


class ConvertTests(unittest.TestCase):
    def test_record_conforms_to_candidate_shape_no_publication(self):
        out = mod.normalize([row()], destination_id="dst-test",
                            source_id="src-overture", bbox=(-3.7, 40.3, -3.5, 40.5))
        self.assertEqual(len(out), 1)
        item = out[0]
        self.assertEqual(item["status"], "candidate")
        self.assertEqual(item["slug"], item["id"])
        self.assertEqual(item["destination_id"], "dst-test")
        self.assertEqual(item["place_type"], "bookshop")
        self.assertNotIn("summary_original", item)
        self.assertNotIn("verified_at", item)

    def test_outside_area_is_excluded(self):
        out = mod.normalize([row()], destination_id="dst-test",
                            source_id="src-overture", bbox=(10, 10, 20, 20))
        self.assertEqual(out, [])

    def test_all_types_map_to_contract(self):
        for kind, expected in [("library", "library"), ("museum", "museum"),
                               ("historic_site", "historic_site")]:
            data = row()
            data["kind_candidate"] = kind
            out = mod.normalize([data], destination_id="dst-test",
                                source_id="src-overture", bbox=(-3.7, 40.3, -3.5, 40.5))
            self.assertEqual(out[0]["place_type"], expected)

    def test_reject_invalid_destination_and_cross_antimeridian(self):
        with self.assertRaises(ValueError):
            mod.normalize([row()], destination_id="../foo",
                          source_id="src-overture", bbox=(-3.7, 40.3, -3.5, 40.5))
        with self.assertRaises(ValueError):
            mod.normalize([row()], destination_id="dst-test",
                          source_id="src-overture", bbox=(170, -10, -170, 10))

    def test_never_escalates_provider_status_to_approved(self):
        x = row()
        x["status"] = "approved"
        self.assertEqual(mod.normalize([x], destination_id="dst-test",
                                        source_id="src-overture",
                                        bbox=(-3.7, 40.3, -3.5, 40.5)), [])


if __name__ == "__main__":
    unittest.main()
