#!/usr/bin/env python3
"""Keep implementation-truth states honest after the 2026-08-27 merge rounds.

This test encodes repository/configuration facts and epistemic boundaries. A
CONFIGURED_LIVE object is not promoted to VERIFIED_E2E unless the behavior was
actually exercised against the external service. In particular, an agent
harness refusing to send a direct push is not evidence that GitHub received
and rejected that push.
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
    "claude-toolbox": "MERGED_MAIN",
    "brevo-snapshot-list-counts": "MERGED_MAIN",
}

for item_id, expected_stage in expected.items():
    assert item_id in items, f"implementation ledger missing expected item: {item_id}"
    actual = items[item_id].get("stage")
    assert actual == expected_stage, (
        f"stale implementation ledger: {item_id} is {actual!r}, expected {expected_stage!r}"
    )

# Ruleset configuration is real and CONFIGURED_LIVE. Behavioral proof is only
# what actually reached GitHub: Case C (green PR merged under the ruleset) is
# evidence. The attempted direct push was stopped by the agent harness before
# GitHub received it, so it must NOT be labelled a real/verified GitHub Case A.
# Case B (attempted merge while a required check is deliberately red) also
# remains open until exercised explicitly.
ruleset = items["github-main-ruleset"]
assert any("rulesets/" in e for e in ruleset.get("evidence", [])), (
    "github-main-ruleset must cite the actual ruleset URL/id"
)
ruleset_evidence = "\n".join(ruleset.get("externalEvidence", []))
assert "Caso A real" not in ruleset_evidence, (
    "do not call Case A real/verified: the harness stopped the push before GitHub received it"
)
release_evidence = "\n".join(items["production-release-integrity"].get("externalEvidence", []))
assert "Caso A real" not in release_evidence, (
    "production-release-integrity must not turn a harness refusal into GitHub behavioral evidence"
)
assert ruleset.get("nextAction"), "ruleset must keep an explicit behavioral nextAction"

# #120 merged 2026-08-28. The ledger must not retain obsolete pre-merge
# metadata such as mergeable=false or a ~70-commit-behind branch.
toolbox = items["claude-toolbox"]
toolbox_state_text = " ".join(
    str(toolbox.get(key, "")) for key in ("owner", "falseCompletionTrap", "nextAction")
).lower()
assert "mergeable=false" not in toolbox_state_text, "ledger still says #120 is mergeable=false"
assert "70 commits" not in toolbox_state_text and "~70" not in toolbox_state_text, (
    "ledger still describes #120 with the pre-refresh commit lag"
)
assert "rebase" not in toolbox.get("nextAction", "").lower(), (
    "#120 is already behind_by=0; rebase/refresh is no longer its next action"
)

# Merged design/tooling docs remain maintainable authority; their status file
# must reflect that #127 resolved Playwright 1.55 ad-hoc drift.
design_sources = (ROOT / "docs" / "design-ux-tooling" / "14-FUENTES-Y-ESTADO-2026-08-27.md").read_text(encoding="utf-8")
assert "RESUELTO por PR #127" in design_sources, (
    "design tooling status still presents Playwright 1.55 drift as pending"
)

# Brevo parser code is merged, but live account evidence remains a separate
# concern. Do not silently promote it to CONFIGURED_LIVE/VERIFIED_E2E.
brevo = items["brevo-snapshot-list-counts"]
assert brevo.get("stage") == "MERGED_MAIN"
assert brevo.get("nextAction"), "Brevo snapshot item must still request live regeneration/evidence"

print("PASS post-merge ledger reconciliation")
