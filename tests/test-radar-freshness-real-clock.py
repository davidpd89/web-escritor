#!/usr/bin/env python3
"""Regression test: radar freshness must use the real execution clock.

This deliberately proves both sides of the gate without network access:
- an opportunity that is still published after 31 days without verification is rejected;
- the same shape freshly verified today is accepted.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


checker = load_module(
    "check_professional_resources",
    ROOT / "scripts" / "check-professional-resources.py",
)
builder = checker.radar_builder()
source = json.loads((ROOT / "data" / "radar-opportunities.json").read_text(encoding="utf-8"))
assert source["items"], "radar fixture source must contain at least one item"

today = date.today()
base = copy.deepcopy(source["items"][0])
base["published"] = True
base["deadline"] = (today + timedelta(days=60)).isoformat()

stale = copy.deepcopy(base)
stale["verified_at"] = (today - timedelta(days=31)).isoformat()
assert builder.state(stale, today) == "stale"
try:
    checker.check_radar_freshness(builder, [stale], [stale], today, today)
except AssertionError as exc:
    assert "stale for real execution date" in str(exc)
    print("ok mutation: stale published dataset -> FAIL")
else:
    raise AssertionError("stale published dataset incorrectly passed the real-clock gate")

# Once the stale item is omitted from the public output, the same source state is valid.
checker.check_radar_freshness(builder, [stale], [], today, today)
print("ok mutation control: stale hidden item -> PASS")

fresh = copy.deepcopy(base)
fresh["verified_at"] = today.isoformat()
assert builder.state(fresh, today) == "open"
checker.check_radar_freshness(builder, [fresh], [fresh], today, today)
print("ok current: freshly verified dataset -> PASS")

# The repository itself must also agree with the real execution date today.
checker.check_radar()
print("test-radar-freshness-real-clock: OK")
