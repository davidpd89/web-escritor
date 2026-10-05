#!/usr/bin/env python3
"""Canonical civil clock for date-sensitive public content."""
from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

SITE_TIMEZONE = "Europe/Madrid"
_SITE_ZONE = ZoneInfo(SITE_TIMEZONE)


def site_today(now: datetime | None = None) -> date:
    """Return the site's civil date in Europe/Madrid.

    Tests may inject an aware datetime to exercise UTC/day-boundary and DST
    transitions deterministically.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("site_today() requires an aware datetime")
    return now.astimezone(_SITE_ZONE).date()
