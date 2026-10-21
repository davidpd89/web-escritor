"""Focused offline tests for the unpublished atlas data contract.

No real persons' addresses, no network, no Actions and no live site files.
"""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("atlas_contract_check", ROOT / "scripts/atlas_contract_check.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def sample():
    return {
        "schema_version": 1,
        "destinations": [{"id": "dst-world", "status": "candidate", "name": "Ciudad sintética"}],
        "places": [{"id": "lug-library", "status": "candidate", "destination_id": "dst-world",
                    "geo_precision": "unlocated", "source_ids": ["src-official"]}],
        "works": [{"id": "obr-synthetic", "status": "candidate", "author_ids": ["aut-synthetic"]}],
        "authors": [{"id": "aut-synthetic", "status": "candidate"}],
        "adaptations": [{"id": "ada-synthetic", "status": "candidate",
                         "original_work_id": "obr-synthetic"}],
        "sources": [{"id": "src-official"}],
        "relationships": [
            {"id": "rel-synthetic", "place_id": "lug-library", "subject_type": "work",
             "subject_id": "obr-synthetic", "relationship_type": "narrative_explicit",
             "status": "candidate", "source_ids": ["src-official"],
             "evidence_note": "Prueba sintética; sin publicación"}],
        "images": [],
        "routes": []
    }


class AtlasContractTest(unittest.TestCase):
    def test_valid_internal_candidates(self):
        self.assertEqual(mod.problems(sample()), [])

    def test_missing_source_rejected(self):
        data = sample()
        data["relationships"][0]["source_ids"] = ["src-missing"]
        self.assertTrue(any("src-missing" in x for x in mod.problems(data)))

    def test_filming_cannot_be_assigned_to_novel(self):
        data = sample()
        data["relationships"][0]["relationship_type"] = "filming_location"
        self.assertTrue(any("incompatibles" in x for x in mod.problems(data)))

    def test_unlocated_must_not_have_fake_point(self):
        data = sample()
        data["places"][0]["latitude"] = 40
        data["places"][0]["longitude"] = -3
        self.assertTrue(any("unlocated" in x for x in mod.problems(data)))

    def test_approved_relation_needs_proof_and_date(self):
        data = sample()
        data["relationships"][0]["status"] = "approved"
        self.assertTrue(any("exige fecha" in x for x in mod.problems(data)))

    def test_popular_unsupported_claim_never_approved(self):
        data = sample()
        data["relationships"][0].update(
            relationship_type="popular_claim_unverified",
            status="approved", verified_at="2026-10-21"
        )
        self.assertTrue(any("nunca puede aprobarse" in x for x in mod.problems(data)))


if __name__ == "__main__":
    unittest.main()
