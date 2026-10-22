#!/usr/bin/env python3
"""Research-only E6 per-field human-review intent contract (NO publication).

Takes an immutable main snapshot + outputs from E4/E5 + a proposed review
manifest. Checks CAS-style digests, field-specific publisher evidence, state
transitions and generation constraints; produces a REVIEW PACKET only.

A JSON field such as decision="approve" is NOT authenticated GitHub approval.
The eventual production PR must require authenticated GitHub review and a
fresh exact-commit check before applying ANY changes.

This tool performs no HTTP, git/gh calls, file edits, merge or deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

SHA40 = re.compile(r"[a-f0-9]{40}\Z")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TASK = re.compile(r"gpt-[a-f0-9]{20}\Z")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
REVIEW_STATUS = {"approve", "reject"}
FIELDS = {"status"}
POSSIBLE_STATUS = {"open", "closed", "indirect", "award_only", "unknown"}
PROVEN_STATUS = {"open", "closed"}


def fingerprint(obj: object) -> str:
    """Digest of exact parsed JSON values (stable across whitespace/order)."""
    value = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _date(raw: object, field: str) -> date:
    if not isinstance(raw, str) or not DATE.fullmatch(raw):
        raise ValueError(f"Invalid {field} date")
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid {field} date") from exc


def _https(url: object) -> bool:
    """Syntactic HTTPS only; upstream E4 approves the exact domain separately."""
    if not isinstance(url, str) or any(ord(ch) < 32 for ch in url):
        return False
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and bool(p.hostname) and
                p.username is None and p.password is None and
                p.port in (None, 443) and not p.fragment)
    except ValueError:
        return False


def review_intents(directory: dict, evidence: dict, plan: dict, manifest: dict,
                   *, as_of: date) -> dict:
    """Fail-closed suggestions only, no writes, no purported trusted approvals."""
    if (not isinstance(directory.get("publishers"), list)
            or evidence.get("schema_version") != 1
            or plan.get("schema_version") != 1
            or manifest.get("schema_version") != 1):
        raise ValueError("Input schema mismatch")
    for name, report in (("evidence", evidence), ("plan", plan)):
        if report.get("as_of") != as_of.isoformat():
            raise ValueError(f"{name} report is from another day")
    if plan.get("publication_enabled") is not False or plan.get("automated_merges_allowed") is not False:
        raise ValueError("Planner does not promise read-only output")
    if evidence.get("writes_to_public_data") is not False:
        raise ValueError("Evidence report is not read-only")
    sha = manifest.get("main_sha")
    if not isinstance(sha, str) or not SHA40.fullmatch(sha):
        raise ValueError("Expected reviewed 40-hex main commit")
    fingerprints = {
        "directory": fingerprint(directory),
        "evidence": fingerprint(evidence),
        "plan": fingerprint(plan),
    }
    if manifest.get("reviewed_fingerprints") != fingerprints:
        raise ValueError("A reviewed input changed: stale exact-data fingerprint")
    if manifest.get("reviewed_at") != as_of.isoformat():
        raise ValueError("Review date and evidence date mismatch")
    items = manifest.get("decisions")
    if not isinstance(items, list) or len(items) > 100:
        raise ValueError("Decisions must be a bounded array")
    authors = {}
    for row in directory["publishers"]:
        if not isinstance(row, dict) or not isinstance(row.get("slug"), str) or not SLUG.fullmatch(row["slug"]) or row["slug"] in authors:
            raise ValueError("Invalid or duplicate publisher slug")
        authors[row["slug"]] = row
    tasks = {}
    for task in plan.get("tasks", []):
        if (not isinstance(task, dict) or not isinstance(task.get("id"), str)
                or not TASK.fullmatch(task["id"]) or task["id"] in tasks
                or task.get("may_write_public_data") is not False):
            raise ValueError("Malformed or duplicate planner task")
        tasks[task["id"]] = task
    evidence_index = {}
    for row in evidence.get("publishers", []):
        if not isinstance(row, dict) or row.get("publication_allowed") is not False:
            raise ValueError("Evidence record could bypass review")
        slug = row.get("slug")
        for src in row.get("submission_status_candidates", []):
            if (not isinstance(src, dict) or not isinstance(src.get("id"), str)
                    or src["id"] in evidence_index):
                raise ValueError("Malformed or duplicate evidence ID")
            evidence_index[src["id"]] = (slug, src)
    seen = set()
    reviewed = []
    rejected = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {
                "task_id", "publisher_slug", "field", "old_value", "new_value",
                "evidence_ids", "decision"}:
            raise ValueError("Unexpected/missing decision keys")
        slug, task_id, field = item["publisher_slug"], item["task_id"], item["field"]
        key = (slug, field)
        if key in seen or not isinstance(slug, str) or not SLUG.fullmatch(slug):
            raise ValueError("Duplicated or invalid per-field intent")
        seen.add(key)
        if field not in FIELDS:
            raise ValueError("Unsupported field: contacts need separate verified values/schema")
        if task_id not in tasks or tasks[task_id].get("kind") != "review_manuscript_change" or tasks[task_id].get("slug") != slug:
            raise ValueError("Unbound or non-change planner task")
        if slug not in authors:
            raise ValueError("No matching directory publisher")
        row = authors[slug]
        if item["old_value"] != row["status"]:
            raise ValueError("Old value differs from reviewed main (CAS violation)")
        new = item["new_value"]
        if new not in POSSIBLE_STATUS or new not in PROVEN_STATUS or new == row["status"]:
            raise ValueError("Status is unsupported, unproven or unchanged")
        if item["decision"] not in REVIEW_STATUS:
            raise ValueError("Decision must be approve or reject")
        proof_ids = item["evidence_ids"]
        if (not isinstance(proof_ids, list) or not proof_ids
                or len(proof_ids) != len(set(proof_ids))
                or not all(isinstance(s, str) and s in evidence_index for s in proof_ids)):
            raise ValueError("Missing/duplicate unknown evidence IDs")
        if sorted(proof_ids) != sorted(tasks[task_id].get("evidence_ids", [])):
            raise ValueError("Evidence does not match reviewed planner task")
        urls = []
        for proof_id in proof_ids:
            candidate_slug, source = evidence_index[proof_id]
            if (candidate_slug != slug or source.get("scope") != "publisher_specific"
                    or source.get("proposed_status") != new or source.get("expired") is not False
                    or not _https(source.get("source_url"))):
                raise ValueError("Cannot prove status for this entity and scope")
            checked = _date(source.get("checked_at"), "checked_at")
            if checked > as_of or (as_of - checked).days > 45:
                raise ValueError("Evidence too old or in future")
            urls.append(source["source_url"])
        base_fields = ["status", "verified_at", "page_updated_at", "sources", "history",
                       "submission_channel", "submission_url", "direct_submission",
                       "requirements", "public_note"]
        if new == "closed" and row.get("submission_email"):
            base_fields.append("submission_email")
        elif row.get("submission_email"):
            base_fields.append("submission_email_recheck")
        outcome = {
            "task_id": task_id, "publisher_slug": slug,
            "requested_field": "status", "old_value": row["status"],
            "new_value": new, "evidence_ids": sorted(proof_ids),
            "source_urls": sorted(set(urls)),
            "manual_companion_fields": base_fields,
            "reviewer_intent": item["decision"],
            "external_authenticated_review_required": True,
            "trusted_approval_verified": False,
            "may_generate_public_patch": False,
        }
        if item["decision"] == "approve":
            reviewed.append(outcome)
        else:
            rejected.append({"task_id": task_id, "publisher_slug": slug,
                             "reviewer_intent": "reject"})
    return {
        "schema_version": 1, "main_sha": sha, "as_of": as_of.isoformat(),
        "fingerprints": fingerprints,
        "intents_for_external_review": sorted(reviewed, key=lambda x: x["publisher_slug"]),
        "rejected_intents": sorted(rejected, key=lambda x: x["publisher_slug"]),
        "authentication": "NOT_VERIFIED_IN_OFFLINE_FILE",
        "patch_generated": False, "writes_to_public_data": False,
        "automated_merge_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("directory", "evidence", "review-plan", "manifest"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    args = parser.parse_args(argv)
    try:
        payloads = {}
        for name in ("directory", "evidence", "review_plan", "manifest"):
            with getattr(args, name).open(encoding="utf-8") as stream:
                payloads[name] = json.load(stream)
        result = review_intents(payloads["directory"], payloads["evidence"],
                                payloads["review_plan"], payloads["manifest"],
                                as_of=args.as_of)
    except (OSError, TypeError, ValueError) as exc:
        print(f"Invalid review intent (nothing published): {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
