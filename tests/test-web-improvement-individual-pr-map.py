import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "web-improvement-individual-prs-2026-08-29.json"

CATEGORY_COUNTS = {
    "A": 12, "B": 9, "C": 10, "D": 12, "E": 8, "F": 6, "G": 5,
    "H": 6, "I": 5, "J": 6, "K": 5, "L": 4, "M": 5, "N": 3,
    "O": 4, "P": 4, "Q": 4,
}
ALLOWED_STATUSES = {
    "IMPLEMENT_NOW",
    "IMPLEMENT_AFTER_CURRENT_DEBT",
    "ALREADY_COVERED",
    "PARTIAL_AUDIT",
    "CONDITIONAL",
    "EXTERNAL_OPERATION",
    "DEFER",
    "REJECT",
}


def expected_ids():
    return [
        f"{category}.{number}"
        for category, count in CATEGORY_COUNTS.items()
        for number in range(1, count + 1)
    ]


def test_pr135_individual_pr_manifest_is_complete_and_unique():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ideas = data["ideas"]

    assert data["ideaCount"] == 108
    assert len(ideas) == 108

    ids = [item["id"] for item in ideas]
    prs = [item["pr"] for item in ideas]

    assert ids == expected_ids()
    assert len(set(ids)) == 108
    assert len(set(prs)) == 108

    excluded = {int(value) for value in data["ideaPrRange"]["excluded"].keys()}
    expected_prs = [
        value
        for value in range(
            data["ideaPrRange"]["first"],
            data["ideaPrRange"]["last"] + 1,
        )
        if value not in excluded
    ]

    assert prs == expected_prs
    assert len(expected_prs) == 108

    for item in ideas:
        assert item["decisionStatus"] in ALLOWED_STATUSES


def test_pr135_handoff_preserves_truth_state_distinctions():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rules = data["rules"]

    assert rules["individualPrIsDetailedArchaeology"] is True
    assert rules["pr148IsCondensedCoordinator"] is True
    assert rules["documentedDoesNotMeanImplemented"] is True
    assert rules["implementedInPrDoesNotMeanMergedMain"] is True
    assert rules["externalOperationRequiresLiveEvidence"] is True
    assert rules["conditionalRequiresTrigger"] is True

    overrides = {item["id"]: item for item in data["practicalOverrides"]}

    assert overrides["E.7"]["effectiveStatus"] == "PARTIAL_AUDIT"
    assert overrides["E.8"]["mergedMain"] is False
    assert overrides["I.2"]["mergedMain"] is False
    assert overrides["Q.3"]["mergedMain"] is False
