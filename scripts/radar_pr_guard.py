#!/usr/bin/env python3
"""Fail closed before publishing a second radar-clock PR against main.

The scheduled workflow is serialized, but each run previously created a unique
GITHUB_RUN_ID branch even while an earlier generated PR remained open.

With --supersede-stale the workflow closes same-day PRs instead of failing:
runs share one concurrency group without cancellation, so an open same-day PR
always belongs to a finished run whose CI failed (e.g. one external timeout).
Failing closed there left every later run, and main, stale until a human acted.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date


def active_radar_prs(rows: object, today: str) -> list[int]:
    date.fromisoformat(today)
    if not isinstance(rows, list):
        raise ValueError("GitHub PR listing is not an array")
    found: list[int] = []
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("Unexpected PR entry in GitHub response")
        ref, number = item.get("headRefName"), item.get("number")
        if not isinstance(ref, str) or not isinstance(number, int):
            raise ValueError("Missing PR headRefName or number")
        if ref.startswith(f"automation/radar-clock-{today}-"):
            found.append(number)
    return sorted(found)


def check_no_open_radar_pr(today: str, *, run=subprocess.run, supersede: bool = False) -> None:
    result = run(
        ["gh", "pr", "list", "--state", "open", "--base", "main",
         "--limit", "1000", "--json", "number,headRefName"],
        capture_output=True, text=True, check=True,
    )
    existing = active_radar_prs(json.loads(result.stdout), today)
    if existing and supersede:
        for number in existing:
            run(["gh", "pr", "close", str(number), "--delete-branch", "--comment",
                 f"Sustituida por una nueva regeneración del radar para {today}: "
                 "la ejecución que la abrió terminó sin fusionarla."],
                capture_output=True, text=True, check=True)
            print(f"SUPERSEDED stale radar PR #{number}")
        return
    if existing:
        numbers = ", ".join(f"#{number}" for number in existing)
        raise RuntimeError(
            f"Radar PR already open ({numbers}); resolve or close it before "
            f"another clock refresh for {today}. No new branch or PR has been created."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", required=True)
    parser.add_argument("--supersede-stale", action="store_true",
                        help="close same-day PRs left open by finished runs instead of failing")
    args = parser.parse_args()
    try:
        check_no_open_radar_pr(args.today, supersede=args.supersede_stale)
    except (ValueError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise SystemExit(f"RADAR PR GUARD: {exc}") from exc
    print("PASS radar PR guard: no existing open radar-clock PR")
