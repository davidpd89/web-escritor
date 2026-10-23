#!/usr/bin/env python3
"""E5 research: offline, read-only review queue for publisher discovery and contacts.

Inputs are reports from E3/E4 plus the public directory. Outputs are REVIEW
CANDIDATES only: never patches, releases, contact addresses or workflow actions.
The existing reading-catalogue publisher remains the sole writer if a later
engineering PR explicitly integrates an approved implementation.

python scripts/research/gpt_editoriales_review_plan.py \
  --directory data/editoriales.json --identities /path/to/E3.json \
  --evidence /path/to/E4.json --as-of 2026-10-22
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
STATUS = {"open", "closed", "unknown", "indirect", "award_only"}


def _slug(raw: object) -> bool:
    return isinstance(raw, str) and bool(SLUG.fullmatch(raw))


def _task_id(kind: str, slug: str, evidence: list[str]) -> str:
    identity = json.dumps([kind, slug, sorted(set(evidence))],
                          ensure_ascii=False, separators=(",", ":"))
    return "gpt-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


def _evidence_ids(items: object, *, fresh_only: bool = False,
                  purpose: str | None = None) -> list[str]:
    if not isinstance(items, list):
        raise ValueError("Evidence group must be a list")
    values = []
    for item in items:
        if not isinstance(item, dict) or not _slug(item.get("id")):
            raise ValueError("Invalid evidence reference")
        if fresh_only and item.get("expired") is not False:
            continue
        if purpose is not None and item.get("proposed_status") != purpose:
            continue
        values.append(item["id"])
    return sorted(set(values))


def plan(directory: dict, identities: dict, evidence: dict, *,
         as_of: date, max_tasks: int = 25) -> dict:
    """Idempotent plan; never implies human approval from source availability."""
    if not 1 <= max_tasks <= 100:
        raise ValueError("max_tasks out of range")
    if (identities.get("as_of") != as_of.isoformat()
            or evidence.get("as_of") != as_of.isoformat()):
        raise ValueError("Stale or mismatched E3/E4 reports; refresh both first")
    rows = directory.get("publishers")
    candidates = identities.get("imprint_candidates")
    contacts = evidence.get("publishers")
    if not all(isinstance(x, list) for x in (rows, candidates, contacts)):
        raise ValueError("Missing directory/candidate/evidence arrays")
    if (identities.get("publish_changes") is not False
            or evidence.get("writes_to_public_data") is not False):
        raise ValueError("Non-research producer would bypass review")
    manual = {}
    for row in rows:
        if not isinstance(row, dict) or not _slug(row.get("slug")):
            raise ValueError("Invalid existing publisher identity")
        if row["slug"] in manual or row.get("status") not in STATUS:
            raise ValueError("Duplicate publisher slug or invalid intake status")
        manual[row["slug"]] = row
    tasks = []
    seen = set()
    deferred = []

    def add(kind: str, slug: str, ids: list[str], priority: int, reason: str):
        if not _slug(slug):
            raise ValueError("Invalid candidate slug")
        key = (kind, slug)
        if key in seen:
            raise ValueError("Duplicate action for publisher")
        seen.add(key)
        tasks.append({
            "id": _task_id(kind, slug, ids), "kind": kind,
            "slug": slug, "priority": priority, "evidence_ids": ids,
            "reason": reason, "requires_human_review": True,
            "may_write_public_data": False
        })

    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Malformed imprint candidate")
        slug = candidate.get("catalogue_slug")
        if not _slug(slug):
            raise ValueError("Invalid imprint slug")
        decision = candidate.get("decision")
        linked = candidate.get("linked_books")
        if type(linked) is not int or linked < 0:
            raise ValueError("Invalid linked-book count")
        if candidate.get("orphan") is not (linked == 0):
            raise ValueError("Inconsistent orphan flag")
        if linked == 0:
            deferred.append({"slug": slug, "reason": "imprint_has_no_published_books"})
            continue
        if (decision == "catalogue_only" and
                candidate.get("bibliographic_source_valid") is True):
            add("verify_new_imprint", slug, [], 3,
                "Published books link to a catalogue-only imprint; identity and evidence still need approval")
        else:
            add("resolve_identity_conflict", slug, [], 0,
                "Alias, collision or untrusted bibliography; refuse automatic identity merge")

    contact_slugs = set()
    for item in contacts:
        if not isinstance(item, dict) or not _slug(item.get("slug")):
            raise ValueError("Malformed contact review record")
        if item.get("manual_review_required") is not True or item.get("publication_allowed") is not False:
            raise ValueError("Contact report is not review-only")
        slug = item["slug"]
        if slug in contact_slugs:
            raise ValueError("Duplicate contact publisher")
        contact_slugs.add(slug)
        if slug not in manual:
            add("unknown_contact_entity", slug, [], 0,
                "Contact refers to absent publisher; never create automatically")
            continue
        current = manual[slug]["status"]
        candidate = item.get("proposed_manuscript_status")
        status_evidence = item.get("submission_status_candidates")
        if candidate == "conflict_review":
            ids = _evidence_ids(status_evidence)
            add("resolve_manuscript_conflict", slug, ids, 0,
                "Contradictory fresh official observations require a human decision")
        elif candidate in ("open", "closed"):
            fresh = _evidence_ids(status_evidence, fresh_only=True, purpose=candidate)
            if not fresh:
                raise ValueError("Status update without fresh explicit publisher-specific proof")
            specific = [s for s in status_evidence
                        if s.get("id") in fresh and s.get("scope") == "publisher_specific"]
            if not specific:
                raise ValueError("Group channel cannot confer an individual status")
            if current != candidate:
                add("review_manuscript_change", slug, fresh, 1,
                    f"Current directory status {current!r} differs from reviewed candidate {candidate!r}")
        elif candidate == "not_inferred":
            old = [s for s in status_evidence or []
                   if isinstance(s, dict) and s.get("expired") is True]
            if old:
                add("recheck_expired_submission_evidence", slug,
                    _evidence_ids(old), 2,
                    "Expired evidence requires another visit; never flip to closed")
        else:
            raise ValueError("Unsupported manuscript status proposal")
        contact_ids = []
        for field in ("general_sources", "press_sources"):
            contact_ids.extend(_evidence_ids(item.get(field), fresh_only=True))
        if contact_ids:
            add("review_contact_channels", slug, sorted(set(contact_ids)), 4,
                "Contact channels require purpose/source check; no email is auto-imported")

    # Revisits for records with ageing manual proof. Status never changes here.
    # Avoid a redundant revisit when a fresh status-change/conflict task exists.
    for slug, row in sorted(manual.items()):
        current = row["status"]
        raw_checked = row.get("verified_at")
        try:
            checked = date.fromisoformat(raw_checked) if isinstance(raw_checked, str) else None
        except ValueError:
            checked = None
        age = (as_of - checked).days if checked else None
        pending_status = any(t["slug"] == slug and t["kind"] in {
            "review_manuscript_change", "resolve_manuscript_conflict",
            "recheck_expired_submission_evidence"} for t in tasks)
        if pending_status:
            continue
        threshold = 90 if current == "unknown" else 45
        if age is None or age < 0 or age > threshold:
            add("reverify_directory_status", slug, [], 5,
                "Current reception claim lacks a recent check; schedule manual verification, not an automatic status change")

    tasks.sort(key=lambda item: (item["priority"], item["slug"], item["kind"], item["id"]))
    integrity = identities.get("integrity_errors")
    collisions = identities.get("duplicate_normalized_directory_names")
    if not isinstance(integrity, list) or not isinstance(collisions, dict):
        raise ValueError("Missing identity integrity gates")
    blockers = []
    if integrity:
        blockers.append("book_publisher_references_broken")
    if collisions:
        blockers.append("duplicate_directory_names")
    if any(t["kind"] in {"resolve_identity_conflict", "resolve_manuscript_conflict",
                         "unknown_contact_entity"} for t in tasks):
        blockers.append("unresolved_identity_or_status_conflicts")
    return {
        "schema_version": 1, "as_of": as_of.isoformat(),
        "mode": "offline_review_plan_only",
        "tasks": tasks[:max_tasks], "deferred": sorted(deferred, key=lambda x: x["slug"]),
        "review_tasks_total": len(tasks),
        "review_tasks_not_emitted": max(0, len(tasks) - max_tasks),
        "blocking_reasons": blockers,
        "publication_enabled": False,
        "automated_merges_allowed": False,
        "http_requests_budget": 0,
        "next_step": "Human verification then separate integration PR against current main",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--identities", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--as-of", type=date.fromisoformat, required=True)
    p.add_argument("--max-tasks", type=int, default=25)
    opts = p.parse_args(argv)
    try:
        with opts.directory.open(encoding="utf-8") as h:
            directory = json.load(h)
        with opts.identities.open(encoding="utf-8") as h:
            identities = json.load(h)
        with opts.evidence.open(encoding="utf-8") as h:
            evidence = json.load(h)
        result = plan(directory, identities, evidence,
                      as_of=opts.as_of, max_tasks=opts.max_tasks)
    except (OSError, ValueError, TypeError) as exc:
        print(f"Research planner rejected its inputs: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
