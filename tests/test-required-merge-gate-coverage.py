#!/usr/bin/env python3
"""The ruleset-required merge gate must cover universal engine contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "required-merge-gate.yml").read_text(encoding="utf-8")

required_fragments = [
    "name: Required merge gate",
    "scripts/requirements.txt",
    "for f in tests/test-*.py",
    "for f in tests/*.mjs",
    "python tests/test-release-identity.py",
    "python tests/test-public-artifact-contract.py",
    "python tests/test-staging-publication-gate.py",
    "python scripts/build-public-dist.py --check-contents",
]
missing = [fragment for fragment in required_fragments if fragment not in workflow]
assert not missing, (
    "Required merge gate lost universal/release contracts that main's ruleset relies on: "
    + ", ".join(missing)
)

print("PASS required merge gate universal coverage")
