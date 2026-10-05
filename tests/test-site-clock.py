#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from site_clock import SITE_TIMEZONE, site_today  # noqa: E402

assert SITE_TIMEZONE=="Europe/Madrid"
# CET: at 23:30 UTC Madrid is already on the next civil day.
assert site_today(datetime(2026,1,1,23,30,tzinfo=timezone.utc))==date(2026,1,2)
# CEST: at 22:30 UTC Madrid is already on the next civil day.
assert site_today(datetime(2026,7,1,22,30,tzinfo=timezone.utc))==date(2026,7,2)
# A moment safely within the same civil day stays unchanged.
assert site_today(datetime(2026,10,5,12,0,tzinfo=timezone.utc))==date(2026,10,5)

try:
    site_today(datetime(2026,10,5,12,0))
except ValueError:
    pass
else:
    raise AssertionError("naive datetimes must be rejected instead of silently assuming a timezone")

print("PASS site civil clock: Europe/Madrid across CET/CEST UTC boundaries")
