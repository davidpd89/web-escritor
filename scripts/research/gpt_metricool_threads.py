#!/usr/bin/env python3
"""Inspect a one-day Metricool MCP followers export for Threads, without secrets.

Read-only usage:
    python scripts/research/gpt_metricool_threads.py /private/threads.json

Exact private input contract:
    {"metrics":["THEV01"], "from":"2026-10-21", "to":"2026-10-21",
     "rows":[["123456.0","20261021"]]}

Values shown above are illustrative; do NOT commit real account exports.
This adapter prints a per-network record, never writes a public site file.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

FIELD = "THEV01"


def count(value: object) -> int | None:
    """Metricool LAST uses decimal strings such as '123456.0'; do not round."""
    if value is None:
        return None
    if type(value) not in (str, int):
        raise ValueError("Followers must be an integer, decimal string, or null")
    if isinstance(value, str) and len(value) > 64:
        raise ValueError("Followers value is too long")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Followers are not numeric") from exc
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        raise ValueError("Followers must be a nonnegative whole number")
    return int(number)


def normalize(raw: dict) -> dict:
    """Accept exactly one *complete* reporting day with verified column order."""
    if not isinstance(raw, dict) or set(raw) != {"metrics", "from", "to", "rows"}:
        raise ValueError("Expected metrics/from/to/rows wrapper")
    if raw["metrics"] != [FIELD]:
        raise ValueError("Only THEV01 follower column is supported")
    stamp = raw["to"]
    if (type(stamp) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamp)
            or raw["from"] != stamp):
        raise ValueError("Export exactly one complete local calendar day")
    try:
        day = date.fromisoformat(stamp)
    except ValueError as exc:
        raise ValueError("Invalid reporting date") from exc
    rows = raw["rows"]
    if not isinstance(rows, list):
        raise ValueError("rows must be an array")
    if len(rows) > 1:
        raise ValueError("Duplicate or unexpected rows for a one-day export")
    followers = None
    if rows:
        row = rows[0]
        if not isinstance(row, list) or len(row) != 2 or type(row[1]) is not str:
            raise ValueError("Row must be [followers, YYYYMMDD]")
        if row[1] != day.strftime("%Y%m%d"):
            raise ValueError("Response day differs from the requested day")
        followers = count(row[0])
    return {
        "id": "threads",
        "followers": followers,
        "views_30d": None,
        "impressions_30d": None,
        "observed_at": stamp if followers is not None else None,
        "source": "metricool-mcp-export",
        "status": "ok" if followers is not None else "partial",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Private MCP export; no secrets or raw exports in Git")
    args = parser.parse_args(argv)
    try:
        result = normalize(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        print(f"Metricool export rejected: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
