#!/usr/bin/env python3
"""Normalize *exported* Metricool MCP Threads rows; never request credentials.

Input is a user-supplied JSON object with exactly:
  {"metrics":["THEV01","THEV06"], "from":"YYYY-MM-DD",
   "to":"YYYY-MM-DD", "rows":[[followers, views, "YYYYMMDD"], ...]}

Run: python scripts/research/gpt_metricool_threads.py /path/to/private-export.json
Prints a safe single-network snapshot; does NOT edit the website or commit results.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys

METRICS = ("THEV01", "THEV06")  # Official Metricool connector: followers LAST; views SUM


def count(value):
    """Metricool emits e.g. '2183.0'. Preserve integral values, not floats."""
    if value is None:
        return None
    if type(value) not in (str, int):
        raise ValueError("Metricool count must be an integer/string or null")
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Metricool count not numeric") from exc
    if not parsed.is_finite() or parsed != parsed.to_integral_value() or parsed < 0:
        raise ValueError("Metricool count must be a non-negative integer")
    return int(parsed)


def normalize(raw):
    if not isinstance(raw, dict) or set(raw) != {"metrics", "from", "to", "rows"}:
        raise ValueError("Expected wrapper keys: metrics, from, to, rows")
    if raw["metrics"] != list(METRICS):
        raise ValueError("Column order must be THEV01, THEV06")
    try:
        first = date.fromisoformat(raw["from"])
        last = date.fromisoformat(raw["to"])
    except (TypeError, ValueError) as exc:
        raise ValueError("from/to must be ISO dates") from exc
    if (last - first).days != 29:
        raise ValueError("Window must contain exactly 30 calendar days inclusive")
    if not isinstance(raw["rows"], list):
        raise ValueError("rows must be an array")
    by_day = {}
    for row in raw["rows"]:
        if not isinstance(row, list) or len(row) != 3 or type(row[2]) is not str:
            raise ValueError("Each row must have two values and YYYYMMDD date")
        try:
            day = datetime.strptime(row[2], "%Y%m%d").date()
        except ValueError as exc:
            raise ValueError("Invalid row date") from exc
        if not first <= day <= last or day in by_day:
            raise ValueError("Date outside requested range or duplicate")
        by_day[day] = (count(row[0]), count(row[1]))
    # Followers are a LAST sample. Do not carry forward an earlier day silently.
    followers = by_day.get(last, (None, None))[0]
    # THEV06 is labeled 'Post Views'. Metricool distinguishes the cumulative
    # performance of published posts from views generated in the period.
    # Without proving which definition this connector uses, suppress views_30d.
    expected_days = [first + timedelta(days=i) for i in range(30)]
    valid_views = [by_day[d][1] for d in expected_days if d in by_day and by_day[d][1] is not None]
    return {
        "id": "threads", "followers": followers, "views_30d": None,
        "impressions_30d": None,
        "period": {"from": first.isoformat(), "to": last.isoformat(), "timezone": "Europe/Madrid"},
        "coverage": {"days_with_post_views": len(valid_views), "required_days": 30},
        "views_not_published_reason": "THEV06 not verified as views generated in selected window",
        "observed_at": last.isoformat() if followers is not None else None,
        "source": "metricool-mcp-export", "status": "ok" if followers is not None else "partial",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Private local export; do not commit raw rows")
    args = parser.parse_args(argv)
    try:
        result = normalize(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Metricool export not accepted: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
