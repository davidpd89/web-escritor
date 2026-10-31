#!/usr/bin/env python3
"""Same-day follower counts read from the official public profiles (no login, no keys).

python scripts/research/gpt_social_public.py   # print the records it would contribute

Metricool only reports closed days and lags Instagram and TikTok by about two days,
so a growing account always looked behind. This reads what any visitor sees today:
Instagram, Threads and Facebook render in a headless browser (their counters are
drawn by JavaScript), TikTok and Pinterest embed the count in their HTML, and X is
read through the public fxtwitter mirror. Each network is independent: a failure,
a login wall or an unparseable page simply yields no record, and the snapshot then
falls back to Metricool or the last-good value.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import sys
from urllib.request import Request, urlopen

import gpt_social_compose as compose

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
TIMEOUT = 25
# Rendered pages: an exact count followed by the Spanish label. Abbreviated
# forms ("2,1 mil") are rejected because they are not exact.
RENDERED = ("instagram", "threads", "facebook")
COUNT_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,   ]\d{3})*|\d+)\s+seguidores\b", re.I)
EMBEDDED = {"tiktok": re.compile(r'"followerCount":(\d+)'),
            "pinterest": re.compile(r'"follower_count":(\d+)')}
X_API = "https://api.fxtwitter.com/{handle}"


def source_name(network: str) -> str:
    return f"{network}-public-profile"


def exact_count(text: str) -> int | None:
    match = COUNT_RE.search(text)
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group(1))
    return int(digits) if digits else None


def fetch(url: str) -> str:
    with urlopen(Request(url, headers={"User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9"}),
                 timeout=TIMEOUT) as response:
        return response.read(3_000_000).decode("utf-8", "replace")


def read_embedded(network: str) -> int:
    html = fetch(compose.PROFILES[network])
    if network == "tiktok":
        # The profile's own userInfo block is the first followerCount; check it is ours.
        if f'"uniqueId":"{compose.PROFILES[network].rsplit("@", 1)[1]}"' not in html:
            raise ValueError("TikTok page does not describe the official account")
        match = EMBEDDED[network].search(html)
        if not match:
            raise ValueError("tiktok: no embedded follower count")
        return int(match.group(1))
    counts = {int(n) for n in EMBEDDED[network].findall(html)}
    if len(counts) != 1:
        raise ValueError(f"{network}: ambiguous embedded follower count")
    return counts.pop()


def read_x() -> int:
    handle = compose.PROFILES["x"].rstrip("/").rsplit("/", 1)[1]
    data = json.loads(fetch(X_API.format(handle=handle)))
    user = data.get("user") if isinstance(data, dict) else None
    if not isinstance(user, dict) or str(user.get("screen_name", "")).lower() != handle.lower():
        raise ValueError("X mirror did not return the official account")
    count = user.get("followers")
    if type(count) is not int:
        raise ValueError("X mirror returned no follower count")
    return count


def read_rendered(networks: tuple[str, ...], errors: list[str]) -> dict[str, int]:
    from playwright.sync_api import sync_playwright  # optional dependency, imported lazily

    found = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context(locale="es-ES", user_agent=UA, viewport={"width": 1280, "height": 900})
            for network in networks:
                page = context.new_page()
                try:
                    page.goto(compose.PROFILES[network], wait_until="domcontentloaded", timeout=TIMEOUT * 1000)
                    page.wait_for_timeout(4000)
                    if network == "facebook" and compose.FACEBOOK_PAGE_ID not in page.content():
                        raise ValueError("page is not the official Facebook page")
                    count = exact_count(page.inner_text("body"))
                    if count is None:
                        raise ValueError("no exact follower count on the public page")
                    found[network] = count
                except Exception as exc:  # one network must not block the others
                    errors.append(f"{network} public: {exc}")
                finally:
                    page.close()
        finally:
            browser.close()
    return found


def read(now: datetime, errors: list[str]) -> list[dict]:
    """Return compose-ready records for every network that could be read right now."""
    stamp = now.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    counts: dict[str, int] = {}
    for network in EMBEDDED:
        try:
            counts[network] = read_embedded(network)
        except Exception as exc:
            errors.append(f"{network} public: {exc}")
    try:
        counts["x"] = read_x()
    except Exception as exc:
        errors.append(f"x public: {exc}")
    try:
        counts.update(read_rendered(RENDERED, errors))
    except Exception as exc:  # Playwright missing or browser failed to start
        errors.append(f"rendered public profiles: {exc}")
    return [{"id": network, "source": source_name(network), "status": "ok",
             "followers": count, "observed_at": stamp}
            for network, count in counts.items()]


if __name__ == "__main__":
    problems: list[str] = []
    for record in read(datetime.now(timezone.utc), problems):
        print(record["id"], record["followers"])
    for problem in problems:
        print("warning:", problem, file=sys.stderr)
