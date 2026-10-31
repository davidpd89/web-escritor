#!/usr/bin/env python3
"""Unattended Metricool follower read: official MCP over plain HTTPS, no LLM.

Needs the one-time `gpt_metricool_mcp.py login`. Verifies that the connected
brand's profile handles are the site's official ones before accepting a value,
then reuses the tested one-day normalizer (gpt_metricool_followers).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import gpt_metricool_followers as followers
import gpt_metricool_mcp as mcp
import gpt_social_compose as compose

METRICS = ["THEV01", "IGEV01", "TKEV07", "PIEV09", "FBEV17"]  # Threads, Instagram, TikTok, Pinterest, Facebook
BRAND_FIELD = {"threads": "threadsData", "instagram": "instagramData",
               "tiktok": "tiktokData", "pinterest": "pinterestData",
               "facebook": "facebookData"}  # Facebook: page id, not a handle
TZ = ZoneInfo("Europe/Madrid")


def handle(url: str) -> str:
    return urlparse(url).path.strip("/").lstrip("@").lower()


def closed_day(now: datetime) -> date:
    return (now.astimezone(TZ) - timedelta(days=1)).date()


def verified_networks(brand: dict) -> set[str]:
    """Networks whose connected Metricool handle equals the official profile link."""
    data = brand.get("networksData") or {}
    expected = {net: handle(compose.PROFILES[net]) for net in BRAND_FIELD} | {"facebook": compose.FACEBOOK_PAGE_ID}
    return {net for net, field in BRAND_FIELD.items()
            if str(data.get(field) or "").lstrip("@").lower() == expected[net]}


def pick_brand(brands: list[dict]) -> tuple[dict, set[str]]:
    scored = [(len(verified_networks(b)), b) for b in brands if isinstance(b, dict)]
    if not scored or max(n for n, _ in scored) == 0:
        raise ValueError("no Metricool brand matches the site's official profiles")
    best = max(n for n, _ in scored)
    winners = [b for n, b in scored if n == best]
    if len(winners) != 1:
        raise ValueError("several Metricool brands match equally; refusing to guess")
    return winners[0], verified_networks(winners[0])


def read(now: datetime, client: mcp.McpClient | None = None) -> dict:
    """Return a metricool-follower-candidates batch restricted to verified networks."""
    client = client or mcp.McpClient()
    brands = client.call("getBrandSettings", {})
    brand, ok = pick_brand(brands["data"] if isinstance(brands, dict) else brands)
    day = closed_day(now)
    off = TZ.utcoffset(datetime.combine(day, datetime.min.time(), TZ)).total_seconds() / 3600
    suffix = f"{'+' if off >= 0 else '-'}{int(abs(off)):02d}:00"
    result = client.call("getAnalyticsDataByMetrics", {
        "brandId": str(brand["id"]), "metrics": METRICS,
        "from": f"{day}T00:00:00{suffix}", "to": f"{day}T23:59:59{suffix}"})
    rows = result.get("rows") if isinstance(result, dict) else None
    if not isinstance(rows, list):
        raise ValueError("unexpected Metricool analytics response")
    batch = followers.normalize({"metrics": METRICS, "from": str(day), "to": str(day), "rows": rows})
    batch["records"] = [r for r in batch["records"] if r["id"] in ok]
    return batch
