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
    "instagram": "https://www.instagram.com/davidportodiaz/",
    "tiktok": "https://www.tiktok.com/@davidportoescritor",
    "pinterest": "https://www.pinterest.com/davidportodiaz/",
}
EXPECTED_SOURCES = {"bluesky": "bluesky-public-appview",
                    "mastodon": "mastodon-public-search",
                    "threads": "metricool-mcp-export",
                    "instagram": "metricool-mcp-export",
                    "tiktok": "metricool-mcp-export",
                    "pinterest": "metricool-mcp-export"}
MAX_AGE = timedelta(hours=48)
MAX_INPUT_BYTES = 64_000
MAX_PUBLIC_COUNT = 2**53 - 1  # JSON numbers must remain exact in JS.
OBSERVED_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})\Z")
SOURCE_RE = re.compile(r"[a-z][a-z0-9-]{0,79}\Z")
UNVERIFIED_PERIOD_FIELDS = ("views_30d", "impressions_30d", "interactions_30d")
# Exact set of follower candidates returned by the already-tested #705 reader.
# Public profile URLs and Metricool account handles independently checked.
# Accept Threads, Instagram, TikTok, Pinterest from this connected brand.
# Bluesky retains public AppView; Facebook, X, YouTube remain unverified.
METRICOOL_BATCH_KIND = "metricool-follower-candidates"
METRICOOL_CANDIDATES = frozenset((
    "bluesky", "threads", "instagram", "facebook",
    "tiktok", "pinterest", "youtube", "twitter",
))


def public_records(source: object) -> list[dict]:
    """Unwrap #705's batch; select only independently verified profiles."""
    if not isinstance(source, dict) or source.get("kind") != METRICOOL_BATCH_KIND:
        return [source]
    if set(source) != {"kind", "schema_version", "requested_day", "generated_at", "records"}:
        raise ValueError("Metricool batch has unexpected or missing fields")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("Unsupported Metricool batch schema")
    day = source["requested_day"]
    if not isinstance(day, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise ValueError("Invalid Metricool requested day")
    try:
        date.fromisoformat(day)
    except ValueError as exc:
        raise ValueError("Invalid Metricool calendar day") from exc
    records = source["records"]
    if not isinstance(records, list) or not records:
        raise ValueError("Metricool batch contains no candidates")
    seen = set()
    selected = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Metricool candidate must be a record")
        identity = record.get("id")
        if type(identity) is not str or identity not in METRICOOL_CANDIDATES:
            raise ValueError("Unknown Metricool candidate identity")
        if identity in seen:
            raise ValueError("Duplicate Metricool candidate")
        seen.add(identity)
        if record.get("source") != "metricool-mcp-export":
            raise ValueError("Metricool candidate uses unexpected provider")
        for field in UNVERIFIED_PERIOD_FIELDS:
            if record.get(field) is not None:
                raise ValueError("Unverified period metric in Metricool batch")
        if record.get("followers") is not None and record.get("observed_at") != day:
            raise ValueError("Metricool candidate date differs from batch")
        if identity in ("threads", "instagram", "tiktok", "pinterest"):
            selected.append(record)
    return selected



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
    if name != EXPECTED_SOURCES[key]:
        raise ValueError(f"{key}: wrong provider for network")
    if source.get("status") not in ("ok", "partial"):
        raise ValueError(f"{key}: unexpected source status")
    for field in UNVERIFIED_PERIOD_FIELDS:
        if source.get(field) is not None:
            raise ValueError(f"{key}: {field} not yet licensed for the public aggregate")
    count = source.get("followers")
    if count is not None and (type(count) is not int or not 0 <= count <= MAX_PUBLIC_COUNT):
        raise ValueError(f"{key}: followers must be a nonnegative integer or null")
    stamp = source.get("observed_at")
    if count is not None and stamp is None:
        raise ValueError(f"{key}: a published count must have a sample date")
    observed = observed_utc(stamp) if stamp is not None else None
    if observed is not None and observed > now:
        raise ValueError(f"{key}: future-dated observation, including unfinished Madrid day")
    stale = observed is not None and now - observed > MAX_AGE
    fresh = count is not None and not stale
    # A public JSON file can outlive the collector. Give the browser an
    # absolute deadline; otherwise a cached last-good number looks live.
    valid_until = observed + MAX_AGE if count is not None else None
    return key, {
        "id": key,
        "profile_url": PROFILES[key],
        "followers": count if fresh else None,
        "observed_at": stamp,
        "valid_until": valid_until.isoformat(timespec="seconds").replace("+00:00", "Z") if valid_until else None,
        "source": name,
        "status": "stale" if stale else ("ok" if fresh else "pending"),
    }


def compose(sources: list, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    observed = {}
    for original in sources:
        for source in public_records(original):
            key, normalized = normalize(source, now)
            if key in observed:
                raise ValueError(f"Duplicate network ID: {key}")
            observed[key] = normalized
    networks = [observed.get(key, {
        "id": key, "profile_url": PROFILES[key], "followers": None,
        "observed_at": None, "valid_until": None,
        "source": None, "status": "pending",
    }) for key in PROFILES]
    valid = [n["followers"] for n in networks if n["followers"] is not None]
    if sum(valid) > MAX_PUBLIC_COUNT:
        raise ValueError("Followers total exceeds exact JavaScript integer range")
    # The aggregate must stop displaying when its FIRST component expires,
    # even if no background job runs to refresh the static JSON file.
    deadlines = [n["valid_until"] for n in networks if n["followers"] is not None]
    return {
        "schema_version": 1,
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "networks": networks,
        "totals": {
            "follower_relationships": sum(valid) if valid else None,
            "valid_until": min(deadlines) if deadlines else None,
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
        if args.output and not args.files:
            raise ValueError("Cannot publish without at least one validated source")
        if args.output and any(path.resolve() == args.output.resolve() for path in args.files):
            raise ValueError("Output file cannot overwrite a source snapshot")
        sources = []
        for path in args.files:
            if path.stat().st_size > MAX_INPUT_BYTES:
                raise ValueError("Source file too large")
            sources.append(json.loads(path.read_text(encoding="utf-8")))
        payload = compose(sources)
        if args.output:
            if not any(source["status"] == "ok" for source in payload["networks"]):
                raise ValueError("No fresh verified follower data; preserve last-good output")
            atomic_write(args.output, payload)
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"Social metrics not updated: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
