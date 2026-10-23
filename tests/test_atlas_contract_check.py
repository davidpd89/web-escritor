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


    def test_approved_relation_rejects_unapproved_place_and_work(self):
        data = sample()
        data["relationships"][0].update(status="approved", verified_at="2026-10-21")
        self.assertTrue(any("places='lug-library' no aprobado" in x for x in mod.problems(data)))
        self.assertTrue(any("works='obr-synthetic' no aprobado" in x for x in mod.problems(data)))

    def test_approved_route_cannot_link_candidate_stops(self):
        data = sample()
        data["routes"] = [{"id": "rou-example", "status": "approved",
                           "verified_at": "2026-10-21",
                           "destination_id": "dst-world",
                           "place_ids": ["lug-library"]}]
        issues = mod.problems(data)
        self.assertTrue(any("places='lug-library' no aprobado" in x for x in issues))
        self.assertTrue(any("destinations='dst-world' no aprobado" in x for x in issues))

    def test_approved_place_requires_approved_destination(self):
        data = sample()
        data["places"][0].update(status="approved", verified_at="2026-10-21",
                                 summary_original="Descripción propia")
        issues = mod.problems(data)
        self.assertTrue(any("destinations='dst-world' no aprobado" in x for x in issues))


    def test_approved_place_requires_usable_source_evidence(self):
        data = sample()
        data["destinations"][0].update(status="approved", verified_at="2026-10-21")
        data["places"][0].update(status="approved", verified_at="2026-10-21",
                                 summary_original="Texto editorial original de prueba")
        issues = mod.problems(data)
        self.assertTrue(any("requiere URL, título, fecha y evidencia" in x for x in issues))

    def test_approved_relation_requires_https_source(self):
        data = sample()
        data["destinations"][0].update(status="approved", verified_at="2026-10-21")
        data["places"][0].update(status="approved", verified_at="2026-10-21",
                                 summary_original="Texto original")
        data["works"][0].update(status="approved", verified_at="2026-10-21")
        data["sources"][0].update(url="javascript:alert(1)", title="Malicioso",
                                  retrieved_at="2026-10-21",
                                  evidence_summary="Prueba")
        data["relationships"][0].update(status="approved", verified_at="2026-10-21")
        self.assertTrue(any("requiere URL HTTPS" in x for x in mod.problems(data)))

    def test_invalid_identifier_lists_fail_closed_without_crashing(self):
        data = sample()
        data["places"][0]["source_ids"] = None
        data["works"][0]["author_ids"] = "aut-synthetic"
        data["routes"] = [{"id": "rou-example", "status": "candidate",
                           "destination_id": "dst-world", "place_ids": None}]
        issues = mod.problems(data)
        self.assertTrue(any("source_ids debe ser lista" in x for x in issues))
        self.assertTrue(any("author_ids debe ser lista" in x for x in issues))
        self.assertTrue(any("place_ids debe ser lista" in x for x in issues))

    def test_approved_image_requires_approved_place(self):
        data = sample()
        data["images"] = [{"id": "img-example", "status": "approved",
                           "place_id": "lug-library",
                           "license": "CC BY", "license_url": "https://example.org/license",
                           "attribution": "Autor sintético",
                           "source_url": "https://example.org/image"}]
        self.assertTrue(any("places='lug-library' no aprobado" in x for x in mod.problems(data)))


    def test_source_https_requires_host_and_no_credentials(self):
        self.assertFalse(mod.valid_https_url("https://"))
        self.assertFalse(mod.valid_https_url("https://user:pass@host.test/file"))
        self.assertFalse(mod.valid_https_url("https://host.test/a b"))
        self.assertFalse(mod.valid_https_url("https://host.test:9090/"))
        self.assertFalse(mod.valid_https_url("javascript:alert(1)"))
        self.assertTrue(mod.valid_https_url("https://cultura.example.org/location"))


if __name__ == "__main__":
    unittest.main()
