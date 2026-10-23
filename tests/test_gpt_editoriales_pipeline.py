"""Exercise the retained review tools together on the complete checkout, offline."""
import hashlib
import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 10, 22)


def load_module(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts/research" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepositoryReviewPipelineTests(unittest.TestCase):
    def test_real_directory_catalogue_and_evidence_produce_read_only_queue(self):
        reconcile = load_module("gpt_editoriales_reconcile")
        contacts = load_module("gpt_editoriales_contact_evidence")
        planner = load_module("gpt_editoriales_review_plan")
        paths = [ROOT / "data" / name for name in (
            "editoriales.json", "reading-publishers.json", "reading-catalogue.json")]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        directory, publishers, books = [json.loads(path.read_text(encoding="utf-8"))
                                        for path in paths]
        research = ROOT / "docs/research/gpt"
        observations = json.loads((research / "editoriales-e4-observaciones-2026-10-22.json").read_text(encoding="utf-8"))
        hosts = json.loads((research / "editoriales-e4-trusted-hosts-2026-10-22.json").read_text(encoding="utf-8"))
        identities = reconcile.reconcile(directory, publishers, books, as_of=TODAY)
        evidence = contacts.review(observations, hosts, as_of=TODAY)
        self.assertEqual(identities["integrity_errors"], [])
        self.assertEqual(identities["duplicate_normalized_directory_names"], {})
        self.assertEqual(evidence["rejected_observations"], [])
        self.assertEqual(identities["counts"]["directory_publishers"], len(directory["publishers"]))
        self.assertEqual(identities["counts"]["catalogue_imprints"], len(publishers["editoriales"]))
        self.assertTrue(identities["counts"]["linked_to_catalogue_imprint"] > 0)
        queue = planner.plan(directory, identities, evidence, as_of=TODAY, max_tasks=100)
        self.assertEqual(queue, planner.plan(directory, identities, evidence,
                                             as_of=TODAY, max_tasks=100))
        self.assertTrue(queue["tasks"])
        keys = [(task["kind"], task["slug"]) for task in queue["tasks"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(task["requires_human_review"] for task in queue["tasks"]))
        self.assertTrue(all(task["may_write_public_data"] is False for task in queue["tasks"]))
        self.assertFalse(queue["publication_enabled"])
        self.assertFalse(queue["automated_merges_allowed"])
        self.assertEqual(queue["http_requests_budget"], 0)
        self.assertNotIn("@", json.dumps(queue))
        self.assertFalse(any(task["kind"] == "review_manuscript_change" and
                             task["slug"] == "alfaguara" for task in queue["tasks"]))
        self.assertEqual(before, [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths])


if __name__ == "__main__":
    unittest.main()
