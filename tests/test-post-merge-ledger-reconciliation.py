#!/usr/bin/env python3
"""Require the implementation ledger to reflect the #114-#124 merge batch.

This test intentionally encodes only facts that are provable from repository
state. It does not promote external account/configuration work to LIVE/E2E.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "implementation-truth-ledger.json"

payload = json.loads(LEDGER.read_text(encoding="utf-8"))
items = {item["id"]: item for item in payload.get("items", [])}

expected = {
    "production-release-integrity": "CONFIGURED_LIVE",
    "github-main-ruleset": "CONFIGURED_LIVE",
    "pwa-asset-freshness": "MERGED_MAIN",
    "mobile-reflow-shared-components": "MERGED_MAIN",
    "design-ux-tooling-system": "MERGED_MAIN",
    "repo-hygiene-round-1": "MERGED_MAIN",
    "claude-toolbox": "IMPLEMENTED_IN_PR",
    "brevo-snapshot-list-counts": "MERGED_MAIN",
}

for item_id, expected_stage in expected.items():
    assert item_id in items, f"implementation ledger missing expected item: {item_id}"
    actual = items[item_id].get("stage")
    assert actual == expected_stage, (
        f"stale implementation ledger: {item_id} is {actual!r}, expected {expected_stage!r} "
        "after the audited #114-#124 merge batch"
    )

# Keep the protection gap honest. A CONFIGURED_LIVE ruleset needs real
# evidence it exists (not just a claim), and must not silently jump to
# VERIFIED_E2E before Case B (a red required check actually blocks merge)
# has been demonstrated -- Case A (direct push) and Case C (agent merges a
# green PR unattended) were verified when this stage changed; Case B is
# still open, which is exactly why nextAction must stay explicit.
ruleset = items["github-main-ruleset"]
assert ruleset.get("stage") == "CONFIGURED_LIVE"
assert any("rulesets/" in e for e in ruleset.get("evidence", [])), (
    "github-main-ruleset must cite the actual ruleset URL/id as evidence, not just a claim"
)
assert ruleset.get("nextAction"), "main ruleset gap must keep an explicit nextAction"

# Merged documentation can still be incomplete. The design/tooling item should
# not disappear merely because PR #114 merged; its missing artifacts remain a
# closure concern described by nextAction/closureCriterion.
design = items["design-ux-tooling-system"]
assert design.get("nextAction"), "design/tooling item must retain completion work after merge"
assert design.get("closureCriterion"), "design/tooling item must retain its Definition of Done"

# Brevo parser code is merged, but live account evidence remains a separate
# concern. Do not silently promote it to CONFIGURED_LIVE/VERIFIED_E2E.
brevo = items["brevo-snapshot-list-counts"]
assert brevo.get("stage") == "MERGED_MAIN"
assert brevo.get("nextAction"), "Brevo snapshot item must still request live regeneration/evidence"

print("PASS post-merge ledger reconciliation")
