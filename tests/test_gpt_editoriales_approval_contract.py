"""Prepared E6 offline approval-intent contract cases; NOT EXECUTED.

The test data is synthetic. No emails, API calls, page changes or merge actions.
"""
import importlib.util
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/gpt_editoriales_approval_contract.py"
spec = importlib.util.spec_from_file_location("gpt_editoriales_approval_contract", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
TODAY = date(2026, 10, 22)
MAIN = "a" * 40
TASK_ID = "gpt-" + "b" * 20


def fixtures(*, old="unknown", new="open", email=None, expired=False, scope="publisher_specific"):
    directory = {"publishers": [{
        "slug": "editorial-luna", "name": "Editorial Luna",
        "status": old, "submission_email": email,
        "verified_at": "2026-10-01", "page_updated_at": "2026-10-01",
    }]}
    proof = {"id": "proof-luna", "source_url": "https://editorial-luna.es/manuscritos",
             "proposed_status": new, "expired": expired,
             "checked_at": "2026-10-21", "scope": scope}
    evidence = {"schema_version": 1, "as_of": TODAY.isoformat(),
                "writes_to_public_data": False, "publishers": [{
                    "slug": "editorial-luna", "publication_allowed": False,
                    "submission_status_candidates": [proof]}]}
    plan = {"schema_version": 1, "as_of": TODAY.isoformat(),
            "publication_enabled": False, "automated_merges_allowed": False,
            "tasks": [{
                "id": TASK_ID, "kind": "review_manuscript_change",
                "slug": "editorial-luna", "evidence_ids": ["proof-luna"],
                "may_write_public_data": False}]}
    intent = {
        "task_id": TASK_ID, "publisher_slug": "editorial-luna",
        "field": "status", "old_value": old, "new_value": new,
        "evidence_ids": ["proof-luna"], "decision": "approve",
    }
    manifest = {
        "schema_version": 1, "reviewed_at": TODAY.isoformat(),
        "main_sha": MAIN, "decisions": [intent],
        "reviewed_fingerprints": {
            "directory": mod.fingerprint(directory),
            "evidence": mod.fingerprint(evidence),
            "plan": mod.fingerprint(plan),
        },
    }
    return directory, evidence, plan, manifest


def evaluate(bundle):
    d, e, p, m = bundle
    return mod.review_intents(d, e, p, m, as_of=TODAY)


class ApprovalContractTests(unittest.TestCase):
    def test_status_change_remains_untrusted_and_read_only(self):
        result = evaluate(fixtures())
        self.assertEqual(len(result["intents_for_external_review"]), 1)
        action, = result["intents_for_external_review"]
        self.assertTrue(action["external_authenticated_review_required"])
        self.assertFalse(action["trusted_approval_verified"])
        self.assertFalse(action["may_generate_public_patch"])
        self.assertFalse(result["automated_merge_allowed"])
        self.assertFalse(result["patch_generated"])

    def test_exact_manifest_matches_idempotently(self):
        a = fixtures()
        self.assertEqual(evaluate(a), evaluate(a))

    def test_any_directory_change_invalidates_snapshot(self):
        bundle = fixtures()
        bundle[0]["publishers"][0]["status"] = "closed"
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_any_evidence_change_invalidates_snapshot(self):
        bundle = fixtures()
        bundle[1]["publishers"][0]["submission_status_candidates"][0]["expired"] = True
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_any_task_change_invalidates_snapshot(self):
        bundle = fixtures()
        bundle[2]["tasks"][0]["kind"] = "review_contact_channels"
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_foreign_evidence_cannot_prove_this_publisher(self):
        bundle = fixtures()
        bundle[1]["publishers"][0]["slug"] = "editorial-sol"
        bundle[3]["reviewed_fingerprints"]["evidence"] = mod.fingerprint(bundle[1])
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_group_evidence_does_not_prove_imprint(self):
        bundle = fixtures(scope="group_general")
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_expired_evidence_fails_closed(self):
        bundle = fixtures(expired=True)
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_unsupported_status_cannot_be_invented(self):
        bundle = fixtures(new="indirect")
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_no_status_change_rejected(self):
        bundle = fixtures(old="open", new="open")
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_closing_a_publisher_requires_email_recheck(self):
        result = evaluate(fixtures(old="open", new="closed",
                                   email="send-manuscripts@editorial-luna.es"))
        needed = result["intents_for_external_review"][0]["manual_companion_fields"]
        self.assertIn("submission_email", needed)
        self.assertIn("history", needed)
        self.assertIn("page_updated_at", needed)

    def test_press_contacts_cannot_be_auto_written(self):
        bundle = fixtures()
        bundle[3]["decisions"][0]["field"] = "press_contact"
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_submission_email_cannot_be_auto_written(self):
        bundle = fixtures()
        bundle[3]["decisions"][0]["field"] = "submission_email"
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_mutating_unknown_fields_refused(self):
        bundle = fixtures()
        bundle[3]["decisions"][0]["unreviewed"] = True
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_reject_is_logged_not_applied(self):
        bundle = fixtures()
        bundle[3]["decisions"][0]["decision"] = "reject"
        out = evaluate(bundle)
        self.assertFalse(out["intents_for_external_review"])
        self.assertEqual(out["rejected_intents"][0]["reviewer_intent"], "reject")

    def test_evidence_task_id_mismatch_fails(self):
        bundle = fixtures()
        bundle[3]["decisions"][0]["evidence_ids"] = ["unknown-proof"]
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_forged_task_kind_fails_even_with_rehashed_plan(self):
        bundle = fixtures()
        bundle[2]["tasks"][0]["kind"] = "verify_new_imprint"
        bundle[3]["reviewed_fingerprints"]["plan"] = mod.fingerprint(bundle[2])
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_main_sha_must_be_full_hex(self):
        bundle = fixtures()
        bundle[3]["main_sha"] = "main"
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_wrong_day_fails_closed(self):
        bundle = fixtures()
        bundle[3]["reviewed_at"] = "2026-10-20"
        with self.assertRaises(ValueError):
            evaluate(bundle)

    def test_duplicate_intents_for_same_publisher_field_forbidden(self):
        bundle = fixtures()
        bundle[3]["decisions"].append(bundle[3]["decisions"][0].copy())
        with self.assertRaises(ValueError):
            evaluate(bundle)


if __name__ == "__main__":
    unittest.main()
