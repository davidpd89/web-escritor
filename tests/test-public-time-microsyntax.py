#!/usr/bin/env python3
"""WHATWG HTML <time datetime> microsyntax regression fixtures.

Production audit in check-public-time-semantics.py already scans the live
public corpus. These fixtures catch false greens for impossible standalone
times, weeks, timezone offsets and yearless calendar dates.
"""
from __future__ import annotations

import contextlib
import io
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with contextlib.redirect_stdout(io.StringIO()):
    checker = runpy.run_path(str(ROOT / "scripts" / "check-public-time-semantics.py"))
parse_temporal = checker["parse_temporal"]

VALID = {
    "23:59": "time at end of day",
    "12:34:59.999": "last valid millisecond",
    "02-29": "leap day in yearless date",
    "--02-29": "yearless date with optional prefix",
    "04-30": "thirty-day month",
    "2020-W53": "actual ISO week 53",
    "2025-W52": "last week of a normal 52-week year",
    "+23:59": "largest allowed offset",
    "-05:30": "negative offset",
    "+00:00": "explicit UTC as positive offset",
    "Z": "UTC offset",
}

INVALID = {
    "24:00": "hour above 23",
    "12:60": "minute above 59",
    "12:34:60": "second above 59",
    "12:34:12.1234": "time fraction above three digits",
    "02-30": "February never has 30 days",
    "--04-31": "April never has 31 days",
    "2025-W53": "ISO week 53 does not exist in 2025",
    "2024-W00": "ISO week zero",
    "+24:00": "offset hour above 23",
    "-08:60": "offset minute above 59",
    "-00:00": "negative zero offset forbidden by HTML standard",
}

problems: list[str] = []
for raw, reason in VALID.items():
    try:
        kind, _ = parse_temporal(raw, html_time=True)
        if kind != "html-only":
            problems.append(f"valid {raw}: expected html-only, got {kind} ({reason})")
    except ValueError as exc:
        problems.append(f"valid {raw}: rejected {exc} ({reason})")

for raw, reason in INVALID.items():
    try:
        actual = parse_temporal(raw, html_time=True)
    except ValueError:
        continue
    problems.append(f"invalid {raw}: accepted {actual!r} ({reason})")

if problems:
    print("FAIL WHATWG time microsyntax regression")
    for item in problems:
        print(" -", item)
    raise SystemExit(1)

print(f"PASS WHATWG time microsyntax regression: {len(VALID)} valid, {len(INVALID)} invalid")
