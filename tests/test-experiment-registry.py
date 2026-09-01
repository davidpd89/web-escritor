#!/usr/bin/env python3
"""Regression tests for the lightweight Q.3 experiment-registry checker."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-experiment-registry.py"
REGISTRY = ROOT / "data" / "experiments.json"


def run_checker(payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "experiments.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(CHECKER), str(path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )


def assert_fails(payload: dict, expected: str) -> None:
    result = run_checker(payload)
    output = result.stdout + result.stderr
    if result.returncode == 0 or expected not in output:
        raise AssertionError(
            f"expected checker failure containing {expected!r}; "
            f"returncode={result.returncode}, output={output!r}"
        )


baseline = json.loads(REGISTRY.read_text(encoding="utf-8"))
valid = run_checker(baseline)
if valid.returncode != 0:
    raise AssertionError(f"historical empty baseline must be valid: {valid.stdout}{valid.stderr}")

entry = {
    "id": "portal-fantasy-ctr",
    "hypothesis": "Un snippet más preciso mejora el CTR sin degradar posición.",
    "baseline": {"query": "portal fantasy", "source": "Search Console"},
    "decision": None,
}

with_duplicate = {**baseline, "experiments": [entry, dict(entry)]}
assert_fails(with_duplicate, "duplicate experiment id")

with_invalid_decision = {
    **baseline,
    "experiments": [{**entry, "id": "invalid-decision", "decision": "WINNER"}],
}
assert_fails(with_invalid_decision, "decision must be null/omitted")

with_incomplete = {
    **baseline,
    "experiments": [{"id": "missing-baseline", "hypothesis": "Hipótesis definida"}],
}
assert_fails(with_incomplete, ".baseline is required")

print("test-experiment-registry: OK (baseline + 3 negative cases)")
