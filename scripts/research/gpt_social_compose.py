#!/usr/bin/env python3
"""Research-only social-stats compositor (three verified links, no API calls).

python scripts/research/gpt_social_compose.py snapshot-bluesky.json snapshot-threads.json
python scripts/research/gpt_social_compose.py snapshot-*.json --output /tmp/social-metrics.json

Input: one JSON object per source, as produced by PRs #705, #706 and #707.
Output: a small, non-sensitive, auditable public JSON contract; stdout by default.
No changes to the published site, navigation, build chain, or Actions.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from zoneinfo import ZoneInfo

# Verified against autor.html and scripts/build-site-shell.py (main, 22/10/2026).
PROFILES = {
    "bluesky": "https://bsky.app/profile/davidportoescritor.bsky.social",
    "mastodon": "https://mastodon.social/@davidportodiaz",
    "threads": "https://www.threads.com/@davidportodiaz",
}
MAX_AGE = timedelta(hours=48)
MAX_INPUT_BYTES = 64_000
OBSERVED_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})\Z")
SOURCE_RE = re.compile(r"[a-z][a-z0-9-]{0,79}\Z")
UNVERIFIED_PERIOD_FIELDS = ("views_30d", "impressions_30d", "interactions_30d")


def observed_utc(value: object) -> datetime:
    """Accept UTC timestamp or end-of-day Madrid date (Metricool daily LAST)."""
    if not isinstance(value, str):
        raise ValueError("observed_at must be an ISO timestamp or day")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        day = date.fromisoformat(value)
        return datetime.combine(day, time.max, tzinfo=ZoneInfo("Europe/Madrid")).astimezone(timezone.utc)
    if not OBSERVED_RE.fullmatch(value):
        raise ValueError("observed_at must include an explicit timezone")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc)


def normalize(source: object, now: datetime) -> tuple[str, dict]:
    if not isinstance(source, dict):
        raise ValueError("Each source must be a JSON object")
    key = source.get("id")
    if type(key) is not str or key not in PROFILES:
        raise ValueError("Unknown network ID; verify canonical account before adding it")
    if "profile_url" in source and source["profile_url"] != PROFILES[key]:
        raise ValueError(f"{key}: supplied profile URL does not match official link")
    name = source.get("source")
    if not isinstance(name, str) or not SOURCE_RE.fullmatch(name):
        raise ValueError(f"{key}: source must be a short nonempty identifier")
    if source.get("status") not in ("ok", "partial"):
        raise ValueError(f"{key}: unexpected source status")
    for field in UNVERIFIED_PERIOD_FIELDS:
        if source.get(field) is not None:
            raise ValueError(f"{key}: {field} not yet licensed for the public aggregate")
    count = source.get("followers")
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError(f"{key}: followers must be a nonnegative integer or null")
    stamp = source.get("observed_at")
    if count is not None and stamp is None:
        raise ValueError(f"{key}: a published count must have a sample date")
    observed = observed_utc(stamp) if stamp is not None else None
    if observed is not None and observed > now:
        raise ValueError(f"{key}: future-dated observation, including unfinished Madrid day")
    stale = observed is not None and now - observed > MAX_AGE
    fresh = count is not None and not stale
    return key, {
        "id": key,
        "profile_url": PROFILES[key],
        "followers": count if fresh else None,
        "observed_at": stamp,
        "source": name,
        "status": "stale" if stale else ("ok" if fresh else "pending"),
    }


def compose(sources: list, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    observed = {}
    for source in sources:
        key, normalized = normalize(source, now)
        if key in observed:
            raise ValueError(f"Duplicate network ID: {key}")
        observed[key] = normalized
    networks = [observed.get(key, {
        "id": key, "profile_url": PROFILES[key], "followers": None,
        "observed_at": None, "source": None, "status": "pending",
    }) for key in PROFILES]
    valid = [n["followers"] for n in networks if n["followers"] is not None]
    return {
        "schema_version": 1,
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "networks": networks,
        "totals": {
            "follower_relationships": sum(valid) if valid else None,
            "coverage": len(valid),
            "eligible": len(PROFILES),
            "label": "Seguidores sumados en redes con datos vigentes (no personas únicas)",
        },
    }


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".social-metrics-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path, help="Validated, private per-network JSON snapshots")
    parser.add_argument("--output", type=Path, help="Explicit file to create atomically; default stdout")
    args = parser.parse_args(argv)
    try:
        sources = []
        for path in args.files:
            if path.stat().st_size > MAX_INPUT_BYTES:
                raise ValueError("Source file too large")
            sources.append(json.loads(path.read_text(encoding="utf-8")))
        payload = compose(sources)
        if args.output:
            atomic_write(args.output, payload)
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"Social metrics not updated: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
