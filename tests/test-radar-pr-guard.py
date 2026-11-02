#!/usr/bin/env python3
"""Behavioural regression for duplicate radar PR prevention; offline and deterministic."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("radar_pr_guard", ROOT / "scripts/radar_pr_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def fake_run(rows, *, error=None):
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        if error:
            raise error
        return subprocess.CompletedProcess(command, 0, json.dumps(rows))
    return run, calls


def verify(rows, expected, today='2026-10-23'):
    run, calls = fake_run(rows)
    try:
        guard.check_no_open_radar_pr(today, run=run)
    except RuntimeError as exc:
        assert expected, f"Unexpected rejection: {exc}"
        assert all(f"#{number}" in str(exc) for number in expected), str(exc)
        assert "No new branch" in str(exc), str(exc)
    else:
        assert not expected, f"Existing PRs were ignored: {expected}"
    assert len(calls) == 1
    argv, options = calls[0]
    assert argv[:3] == ["gh", "pr", "list"]
    assert argv[argv.index("--state") + 1] == "open"
    assert argv[argv.index("--base") + 1] == "main"
    assert argv[argv.index("--json") + 1] == "number,headRefName"
    assert options["check"] and options["capture_output"] and options["text"]
    assert not any(command in argv for command in ("create", "push", "merge", "close"))


verify([], [])
verify([{"number": 5, "headRefName": "automation/reading-catalogue-2026"}], [])
verify([{"number": 730, "headRefName": "automation/radar-clock-2026-10-23-manual"}], [730])
verify([{"number": 689, "headRefName": "automation/radar-clock-2026-10-22-39701259246"}], [])
verify([
    {"number": 730, "headRefName": "automation/radar-clock-2026-10-23-manual"},
    {"number": 731, "headRefName": "automation/radar-clock-2026-10-23-39900000000"},
    {"number": 33, "headRefName": "feature/radar-clock-design"},
], [730, 731])

for malformed in (None, {}, [None], [{"number": 10}], [{"headRefName": "automation/radar-clock-2026-10-23"}]):
    try:
        guard.active_radar_prs(malformed, '2026-10-23')
    except ValueError:
        pass
    else:
        raise AssertionError(f"Malformed GitHub response accepted: {malformed!r}")

run, _ = fake_run([], error=subprocess.CalledProcessError(1, ["gh", "pr", "list"]))
try:
    guard.check_no_open_radar_pr('2026-10-23', run=run)
except subprocess.CalledProcessError:
    pass
else:
    raise AssertionError("GitHub listing failure must stop publication")

rows = [
    {"number": 730, "headRefName": "automation/radar-clock-2026-10-23-manual"},
    {"number": 689, "headRefName": "automation/radar-clock-2026-10-22-39701259246"},
]
run, calls = fake_run(rows)
guard.check_no_open_radar_pr('2026-10-23', run=run, supersede=True)
closes = [argv for argv, _ in calls if argv[:3] == ["gh", "pr", "close"]]
assert [argv[3] for argv in closes] == ["730"], closes  # Only today's PR; other days are never touched.
assert all("--delete-branch" in argv and "--comment" in argv for argv in closes)
assert all(options["check"] for _, options in calls)
run, calls = fake_run([])
guard.check_no_open_radar_pr('2026-10-23', run=run, supersede=True)
assert len(calls) == 1

workflow = (ROOT / ".github/workflows/radar-clock-refresh.yml").read_text(encoding="utf-8")
assert 'python scripts/radar_pr_guard.py --supersede-stale --today "${{ steps.clock.outputs.today }}"' in workflow
assert workflow.index("python scripts/radar_pr_guard.py") < workflow.index('git switch -c "$branch"')
assert "GITHUB_RUN_ID" in workflow  # Serialized runs still use independent branches.
# Superseding is only safe while no other run can be in flight.
assert "group: refresh-radar-clock" in workflow and "cancel-in-progress: false" in workflow
print("PASS radar same-day PR guard: 5 scenarios, stale same-day PR superseded, malformed input, API failure, guard before branch creation")
