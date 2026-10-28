#!/usr/bin/env python3
"""WHATWG HTML duration conformance; keep JSON-LD calendar durations distinct."""
from __future__ import annotations

import contextlib
import io
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with contextlib.redirect_stdout(io.StringIO()):
    temporal = runpy.run_path(str(ROOT / "scripts/check-public-time-semantics.py"))
parse_temporal = temporal["parse_temporal"]

HTML_VALID = (
    "P1D", "PT2H", "PT20M", "PT0S", "PT1.5S",
    "P1DT2H3M4.125S", "P12D", "2h 30m", "1W", "1d2H",
    "4m3s", "2.25s", "0s",
)
HTML_INVALID = (
    "P", "PT", "P1DT", "P1Y", "P2M", "P1W", "P1D2H",
    "PT1.1234S", "P1DT2H3M4.1234S", "PT1Y",
    "2h 3h", "1w2W", "2.5h", "1.2345s", "2y",
    "-1h", "1ms", "1 hour",
)
SCHEMA_CALENDAR_VALID = ("P1Y", "P2M", "P1W", "PT2H", "P1D")

failures: list[str] = []
for value in HTML_VALID:
    try:
        kind, _ = parse_temporal(value, html_time=True)
        if kind != "duration":
            failures.append(f"HTML valid {value!r}: returned {kind!r}")
    except ValueError as exc:
        failures.append(f"HTML valid {value!r}: {exc}")

for value in HTML_INVALID:
    try:
        result = parse_temporal(value, html_time=True)
        failures.append(f"HTML invalid {value!r}: accepted {result!r}")
    except ValueError:
        pass

for value in SCHEMA_CALENDAR_VALID:
    try:
        kind, _ = parse_temporal(value, html_time=False)
        if kind != "duration":
            failures.append(f"Schema.org ISO {value!r}: returned {kind!r}")
    except ValueError as exc:
        failures.append(f"Schema.org ISO {value!r}: {exc}")

if failures:
    print("FAIL HTML duration microsyntax and Schema.org compatibility")
    for failure in failures:
        print(" -", failure)
    raise SystemExit(1)

print(
    "PASS HTML duration microsyntax and Schema.org compatibility: "
    f"{len(HTML_VALID)} positive + {len(HTML_INVALID)} negative + "
    f"{len(SCHEMA_CALENDAR_VALID)} ISO compatibility"
)
