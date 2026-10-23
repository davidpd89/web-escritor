#!/usr/bin/env python3
"""Regression: skip-CI markers must be rejected before a squash merge."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("skipci", ROOT / "scripts" / "check-no-skip-ci-markers.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

for bad in ("docs: x [skip ci]", "x [CI SKIP]", "y [skip actions]", "z\n\nskip-checks: true"):
    assert mod.find_markers([("c", bad)]), bad
for ok in ("feat: skip ci tooling docs", "fix: skip checks list", "", None):
    assert not mod.find_markers([("c", ok)]), ok

gate = (ROOT / ".github" / "workflows" / "required-merge-gate.yml").read_text(encoding="utf-8")
assert "scripts/check-no-skip-ci-markers.py" in gate, "gate must run the skip-ci marker check"
print("PASS skip-ci marker guard")
