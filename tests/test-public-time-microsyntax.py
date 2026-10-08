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
    "2026-10-08T12:34:56.123Z": "global datetime with three decimal places",
    "2026-10-08 12:34+02:00": "local/global datetime with a space separator",
    "2026-10-08T12:34": "valid local date and time without timezone",
    "2026-10-08 12:34:39": "valid local date with space and seconds",
    "2026-10-08T12:34:39.929": "valid local date with milliseconds",
    "12345-01-01T00:00": "five-digit year as local datetime",
    "12345-01-01T00:00Z": "five-digit year as global datetime",
    "10000-02-29T12:34Z": "five-digit leap-year HTML datetime",
    "10000-02-29": "standalone valid five-digit leap date",
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
    "2026-10-08T12:34:56.1234Z": "four decimal places are not valid in HTML",
    "2026-10-08T12:34-00:00": "full datetime cannot use negative-zero timezone",
    "2026-10-08T12:34+2400": "full datetime offset beyond 23 hours",
    "0000-01-01T00:00": "zero year invalid in local HTML datetime",
    "0000-01-01T00:00Z": "zero year invalid in global HTML datetime",
    "10001-02-29T12:34Z": "non-leap five-digit year cannot have February 29",
    "10001-02-29": "standalone invalid five-digit leap date",
}

problems: list[str] = []
for raw, reason in VALID.items():
    try:
        kind, _ = parse_temporal(raw, html_time=True)
        expected_kind = "datetime" if raw.startswith("2026-") else "html-only"
        if kind != expected_kind:
            problems.append(f"valid {raw}: expected {expected_kind}, got {kind} ({reason})")
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
