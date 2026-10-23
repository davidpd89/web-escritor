#!/usr/bin/env python3
"""Normalize a one-day Metricool MCP export for multiple follower counters.

Pass JSON containing {"metrics":[field IDs], "from":"YYYY-MM-DD",
"to":"YYYY-MM-DD", "rows":[[value1,...,valueN,"YYYYMMDD"]]}.
No network/API key; never writes to the public website.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

# Reuse the already-tested date, counter and shape validation from PR #705.
from gpt_metricool_threads import normalize as normalize_one

FIELDS = {
    "BKEV01": "bluesky",
    "THEV01": "threads",
    "IGEV01": "instagram",
    "FBEV17": "facebook",
    "TKEV07": "tiktok",
    "PIEV09": "pinterest",
    "YTEV01": "youtube",
    "TTEV01": "twitter",
}


def normalize(raw: dict) -> dict:
    if not isinstance(raw, dict) or set(raw) != {"metrics", "from", "to", "rows"}:
        raise ValueError("Expected exactly metrics, from, to and rows")
    fields = raw["metrics"]
    if not isinstance(fields, list) or not fields:
        raise ValueError("metrics must be a nonempty list")
    if any(type(field) is not str or field not in FIELDS for field in fields):
        raise ValueError("Unknown or non-follower Metricool metric")
    if len(set(fields)) != len(fields):
        raise ValueError("Repeated field would double-count a network")
    rows = raw["rows"]
    if not isinstance(rows, list) or len(rows) > 1:
        raise ValueError("Expected at most one row for one closed reporting day")
    if rows and (not isinstance(rows[0], list) or len(rows[0]) != len(fields) + 1):
        raise ValueError("Row width does not match requested metrics plus date")
    date_value = rows[0][-1] if rows else None
    records = []
    for i, field in enumerate(fields):
        # The single-field adapter enforces Gregorian date, from=to, row
        # date equality, strict integer/null validation and metric status.
        one = normalize_one({
            "metrics": ["THEV01"],
            "from": raw["from"],
            "to": raw["to"],
            "rows": [[rows[0][i], date_value]] if rows else [],
        })
        one["id"] = FIELDS[field]
        records.append(one)
    return {
        "kind": "metricool-follower-candidates",
        "schema_version": 1,
        "requested_day": raw["to"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Private local export of MCP rows; never commit it")
    args = parser.parse_args(argv)
    try:
        raw = args.input.read_bytes()
        if len(raw) > 64_000:
            raise ValueError("Metricool export unexpectedly large")
        result = normalize(json.loads(raw))
    except (ValueError, OSError) as exc:
        print(f"Metricool follower export not accepted: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
