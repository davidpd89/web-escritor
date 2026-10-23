#!/usr/bin/env python3
"""Fail closed before publishing a second radar-clock PR against main.

The scheduled workflow is serialized, but each run previously created a unique
GITHUB_RUN_ID branch even while an earlier generated PR remained open.
"""
from __future__ import annotations

import json
import subprocess


def active_radar_prs(rows: object) -> list[int]:
    if not isinstance(rows, list):
        raise ValueError("GitHub PR listing is not an array")
    found: list[int] = []
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("Unexpected PR entry in GitHub response")
        ref, number = item.get("headRefName"), item.get("number")
        if not isinstance(ref, str) or not isinstance(number, int):
            raise ValueError("Missing PR headRefName or number")
        if ref.startswith("automation/radar-clock-"):
            found.append(number)
    return sorted(found)


def check_no_open_radar_pr(*, run=subprocess.run) -> None:
    result = run(
        ["gh", "pr", "list", "--state", "open", "--base", "main",
         "--limit", "1000", "--json", "number,headRefName"],
        capture_output=True, text=True, check=True,
    )
    existing = active_radar_prs(json.loads(result.stdout))
    if existing:
        numbers = ", ".join(f"#{number}" for number in existing)
        raise RuntimeError(
            f"Radar PR already open ({numbers}); resolve or close it before "
            "another clock refresh. No new branch or PR has been created."
        )


if __name__ == "__main__":
    try:
        check_no_open_radar_pr()
    except (ValueError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise SystemExit(f"RADAR PR GUARD: {exc}") from exc
    print("PASS radar PR guard: no existing open radar-clock PR")
