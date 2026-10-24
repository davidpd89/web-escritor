"""Offline review planning contracts, including the complete repository data."""
import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/gpt_editoriales_review_plan.py"
spec = importlib.util.spec_from_file_location("gpt_editoriales_review_plan", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
TODAY = date(2026, 10, 22)


def manual(status="unknown", checked="2026-10-21", slug="editorial-uno"):
    return {"slug": slug, "name": "Editorial Uno",
            "status": status, "verified_at": checked,
            "submission_email": "private@example.com"}


def imprint(slug="sello-nuevo", decision="catalogue_only",
            linked=1, valid=True):
    return {"catalogue_slug": slug, "decision": decision,
            "linked_books": linked, "orphan": linked == 0,
            "bibliographic_source_valid": valid}


def identity(*candidates, integrity=None, collisions=None, as_of="2026-10-22"):
    return {"as_of": as_of, "publish_changes": False,
            "imprint_candidates": list(candidates),
            "integrity_errors": integrity or [],
            "duplicate_normalized_directory_names": collisions or {}}


def evidence_record(status="not_inferred", slug="editorial-uno",
                    observations=None, general=None, press=None):
    return {"slug": slug, "proposed_manuscript_status": status,
            "submission_status_candidates": observations or [],
            "general_sources": general or [], "press_sources": press or [],
            "manual_review_required": True, "publication_allowed": False}


def ev(ident="proba-uno", proposed="open", expired=False,
       scope="publisher_specific"):
    return {"id": ident, "proposed_status": proposed,
            "expired": expired, "scope": scope}


def evidence(*rows, as_of="2026-10-22"):
    return {"as_of": as_of, "writes_to_public_data": False,
            "publishers": list(rows)}


def run(*imprints, directory=None, contacts=None, max_tasks=25, identity_overrides=None):
    return mod.plan({"publishers": directory if directory is not None else [manual()]},
                    identity_overrides or identity(*imprints),
                    contacts if contacts is not None else evidence(),
                    as_of=TODAY, max_tasks=max_tasks)


class ReviewPlanningTests(unittest.TestCase):
    def test_duplicate_contact_publishers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate contact publisher"):
            run(contacts=evidence(evidence_record(), evidence_record()))

    def test_new_imprint_is_review_only_and_idempotent(self):
        a = run(imprint())
        b = run(imprint())
        self.assertEqual(a, b)
        task, = a["tasks"]
        self.assertEqual(task["kind"], "verify_new_imprint")
        self.assertTrue(task["requires_human_review"])
        self.assertFalse(task["may_write_public_data"])
        self.assertFalse(a["publication_enabled"])
        self.assertFalse(a["automated_merges_allowed"])
        self.assertEqual(a["http_requests_budget"], 0)

    def test_zero_linked_books_defers_but_does_not_publish(self):
        a = run(imprint(linked=0))
        self.assertEqual(a["tasks"], [])
        self.assertEqual(a["deferred"], [{"slug": "sello-nuevo",
                                         "reason": "imprint_has_no_published_books"}])

    def test_collision_blocks_identity_merge(self):
        a = run(imprint(decision="review_slug_collision"))
        self.assertEqual(a["tasks"][0]["kind"], "resolve_identity_conflict")
        self.assertIn("unresolved_identity_or_status_conflicts", a["blocking_reasons"])

    def test_untrusted_bibliography_requires_conflict_review(self):
        a = run(imprint(valid=False))
        self.assertEqual(a["tasks"][0]["kind"], "resolve_identity_conflict")

    def test_status_change_requires_fresh_publisher_evidence(self):
        e = evidence(evidence_record("open", observations=[ev()]))
        a = run(directory=[manual()], contacts=e)
        t, = a["tasks"]
        self.assertEqual(t["kind"], "review_manuscript_change")
        self.assertEqual(t["evidence_ids"], ["proba-uno"])
        self.assertEqual(t["priority"], 1)

    def test_current_status_same_as_evidence_is_not_a_change(self):
        a = run(directory=[manual(status="open")],
                contacts=evidence(evidence_record("open", observations=[ev()])))
        self.assertEqual(a["tasks"], [])

    def test_group_process_does_not_prove_a_sello_accepts(self):
        with self.assertRaises(ValueError):
            run(contacts=evidence(evidence_record(
                "open", observations=[ev(scope="group_general")])))

    def test_stale_observation_cannot_prove_open(self):
        with self.assertRaises(ValueError):
            run(contacts=evidence(evidence_record(
                "open", observations=[ev(expired=True)])))

    def test_conflicting_statements_block(self):
        a = run(contacts=evidence(evidence_record(
            "conflict_review", observations=[ev(), ev("proba-dos", "closed")])))
        self.assertEqual(a["tasks"][0]["kind"], "resolve_manuscript_conflict")
        self.assertIn("unresolved_identity_or_status_conflicts", a["blocking_reasons"])

    def test_expired_status_means_recheck_not_closed(self):
        a = run(contacts=evidence(evidence_record(
            observations=[ev(expired=True)])))
        self.assertEqual(a["tasks"][0]["kind"], "recheck_expired_submission_evidence")

    def test_general_and_press_are_separate_from_intake(self):
        a = run(contacts=evidence(evidence_record(
            general=[ev("general")], press=[ev("prensa")])))
        t, = a["tasks"]
        self.assertEqual(t["kind"], "review_contact_channels")
        self.assertEqual(t["evidence_ids"], ["general", "prensa"])
        self.assertNotIn("open", json.dumps(a))
        self.assertNotIn("private@example.com", json.dumps(a))

    def test_unknown_publisher_requires_manual_identity(self):
        a = run(contacts=evidence(evidence_record(slug="otra-editorial")))
        self.assertEqual(a["tasks"][0]["kind"], "unknown_contact_entity")

    def test_old_directory_record_gets_recheck_not_auto_closure(self):
        a = run(directory=[manual(status="open", checked="2026-07-01")])
        self.assertEqual(a["tasks"][0]["kind"], "reverify_directory_status")
        self.assertFalse(a["publication_enabled"])

    def test_current_directory_verification_has_no_revisit(self):
        self.assertEqual(run()["tasks"], [])

    def test_old_directory_with_fresh_status_change_has_one_status_action(self):
        a = run(directory=[manual(checked="2026-07-01")],
                contacts=evidence(evidence_record("open", observations=[ev()])))
        self.assertEqual([t["kind"] for t in a["tasks"]], ["review_manuscript_change"])

    def test_mismatched_report_dates_fail_closed(self):
        with self.assertRaises(ValueError):
            run(contacts=evidence(as_of="2026-10-21"))
        with self.assertRaises(ValueError):
            run(identity_overrides=identity(as_of="2026-10-21"))

    def test_non_readonly_producer_is_rejected(self):
        e = evidence()
        e["writes_to_public_data"] = True
        with self.assertRaises(ValueError):
            run(contacts=e)

    def test_corrupted_directory_slugs_are_rejected(self):
        with self.assertRaises(ValueError):
            run(directory=[manual(), manual()])
        with self.assertRaises(ValueError):
            run(directory=[manual(status="yes")])

    def test_broken_references_are_global_blockers(self):
        a = run(identity_overrides=identity(integrity=[{
            "book": "isbn-demo", "problem": "missing_directory_slug"}]))
        self.assertIn("book_publisher_references_broken", a["blocking_reasons"])

    def test_queue_limit_still_counts_deferred_review_tasks(self):
        a = run(*[imprint(slug="sello-" + str(i)) for i in range(12)], max_tasks=4)
        self.assertEqual(len(a["tasks"]), 4)
        self.assertEqual(a["review_tasks_total"], 12)
        self.assertEqual(a["review_tasks_not_emitted"], 8)

    def test_stable_id_does_not_depend_on_queue_limit(self):
        full = run(imprint(), imprint(slug="otro-sello"))
        limited = run(imprint(), imprint(slug="otro-sello"), max_tasks=1)
        self.assertEqual(full["tasks"][0]["id"], limited["tasks"][0]["id"])


if __name__ == "__main__":
    unittest.main()
