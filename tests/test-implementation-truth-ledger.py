#!/usr/bin/env python3
"""Structural/semantic contract for the implementation truth ledger.

The test deliberately does not pretend it can prove external account state from
CI. It enforces the part a repository *can* prove: valid vocabulary, unique
ownership records, evidence requirements, and no 'verified' state without
explicit external evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "implementation-truth-ledger.json"
DOC = ROOT / "docs" / "IMPLEMENTATION-TRUTH-LEDGER-2026-08-27.md"

ALLOWED_STAGES = {
    "DOCUMENTED",
    "IMPLEMENTED_IN_PR",
    "MERGED_MAIN",
    "CONFIGURED_LIVE",
    "VERIFIED_E2E",
    "BLOCKED",
    "NOT_APPLICABLE",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def main() -> None:
    assert LEDGER.is_file(), f"missing ledger: {LEDGER}"
    assert DOC.is_file(), f"missing human authority: {DOC}"

    payload = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert payload.get("schemaVersion") == 1
    assert payload.get("repository") == "davidpd89/web-escritor"

    semantics = payload.get("stageSemantics")
    assert isinstance(semantics, dict)
    assert set(semantics) == ALLOWED_STAGES, "stageSemantics must define every allowed stage exactly once"
    for stage, description in semantics.items():
        assert stage in ALLOWED_STAGES
        assert nonempty_string(description), f"blank semantics for {stage}"

    items = payload.get("items")
    assert isinstance(items, list) and items, "ledger must contain at least one tracked initiative"

    ids: set[str] = set()
    for item in items:
        assert isinstance(item, dict), "each ledger item must be an object"
        item_id = item.get("id")
        assert nonempty_string(item_id), "item id required"
        if item_id in ids:
            fail(f"duplicate ledger id: {item_id}")
        ids.add(item_id)

        for field in ("title", "area", "owner", "falseCompletionTrap", "closureCriterion", "lastVerified"):
            assert nonempty_string(item.get(field)), f"{item_id}: non-empty {field} required"

        stage = item.get("stage")
        assert stage in ALLOWED_STAGES, f"{item_id}: invalid stage {stage!r}"

        evidence = item.get("evidence")
        external = item.get("externalEvidence")
        assert isinstance(evidence, list), f"{item_id}: evidence must be an array"
        assert isinstance(external, list), f"{item_id}: externalEvidence must be an array"
        assert all(nonempty_string(ref) for ref in evidence), f"{item_id}: blank repo evidence entry"
        assert all(nonempty_string(ref) for ref in external), f"{item_id}: blank external evidence entry"

        # A live/verified claim needs evidence outside the repository. A config
        # example, Markdown plan or source test cannot establish account state.
        if stage in {"CONFIGURED_LIVE", "VERIFIED_E2E"}:
            assert external, f"{item_id}: {stage} requires explicit externalEvidence"

        # E2E is the strongest claim: it must also have repository/runbook
        # provenance so someone can reproduce/locate what was tested.
        if stage == "VERIFIED_E2E":
            assert evidence, f"{item_id}: VERIFIED_E2E requires repo/runbook evidence too"

        # Incomplete work must tell the next agent exactly where to continue.
        if stage not in {"VERIFIED_E2E", "NOT_APPLICABLE"}:
            assert nonempty_string(item.get("nextAction")), f"{item_id}: incomplete item requires nextAction"

        # Closure criterion must be more than a restatement of the stage.
        criterion = item["closureCriterion"].strip()
        assert len(criterion) >= 20, f"{item_id}: closureCriterion is too vague"

    # The human doc must preserve the stage vocabulary; otherwise the JSON and
    # prose could drift into two incompatible meanings of 'done'.
    doc = DOC.read_text(encoding="utf-8")
    for stage in ALLOWED_STAGES:
        assert f"`{stage}`" in doc, f"human doc missing stage definition/reference: {stage}"

    # Operational data is deliberately internal. The public builder itself is
    # tested elsewhere; this assertion protects the expected namespace here.
    assert LEDGER.relative_to(ROOT).parts[0] == "data"

    print(f"OK: implementation truth ledger valid ({len(items)} initiatives, {len(ids)} unique ids).")


if __name__ == "__main__":
    main()
