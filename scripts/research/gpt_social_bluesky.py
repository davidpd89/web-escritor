#!/usr/bin/env python3
"""Read one public Bluesky profile and output one normalised social snapshot.

Offline: python scripts/research/gpt_social_bluesky.py --fixture tests/fixtures/social/bluesky_profile.fixture.json
Live:    python scripts/research/gpt_social_bluesky.py --expected-did 'did:plc:...' --output /tmp/bluesky.json

No login, no auto-schedule, no page mutation. This is deliberately isolated.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ACTOR = "davidportoescritor.bsky.social"
API = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile"
PROFILE_URL = "https://bsky.app/profile/" + ACTOR
MAX_BYTES = 256_000


def read_profile(*, timeout: float = 10.0) -> dict:
    """One authentication-free AppView request; no speculative retry or writes."""
    url = API + "?" + urlencode({"actor": ACTOR})
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "web-escritor-social-stats/1.0 (public profile)",
    })
    with urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Bluesky response too large")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError("Bluesky response must be a JSON object")
    return data


def optional_count(value: object) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise ValueError("Bluesky count must be a nonnegative integer or null")
    return value


def normalize_profile(
    data: dict, *, expected_did: str | None = None, observed_at: str | None = None
) -> dict:
    """Reject identity drift and malformed metrics; never fabricate zeros."""
    if not isinstance(data, dict):
        raise ValueError("Profile is not an object")
    handle, did = data.get("handle"), data.get("did")
    if not isinstance(handle, str) or handle.casefold() != ACTOR:
        raise ValueError("Profile handle does not match the canonical account")
    if not isinstance(did, str) or not did.startswith("did:"):
        raise ValueError("Profile DID is invalid")
    if expected_did is not None and did != expected_did:
        raise ValueError("Profile DID changed: stop and verify account ownership")
    followers = optional_count(data.get("followersCount"))
    posts = optional_count(data.get("postsCount"))
    return {
        "id": "bluesky",
        "profile_url": PROFILE_URL,
        "handle": handle,
        "did": did,
        "followers": followers,
        "posts": posts,
        "views_30d": None,
        "impressions_30d": None,
        "interactions_30d": None,
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "bluesky-public-appview",
        "status": "ok" if followers is not None else "partial",
    }


def write_json_atomic(path: Path, snapshot: dict) -> None:
    """Never truncate last-good output on failed validation or file write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".bluesky-", suffix=".tmp", delete=False) as f:
            tmp_path = Path(f.name)
            json.dump(snapshot, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-did", help="Stable account DID, once independently verified")
    parser.add_argument("--output", type=Path, help="Explicit output file; otherwise print JSON")
    parser.add_argument("--fixture", type=Path, help="Offline contract inspection (cannot write output)")
    args = parser.parse_args(argv)
    if args.fixture and args.output:
        parser.error("--fixture cannot be used with --output")
    if args.output and not args.expected_did:
        parser.error("--output requires --expected-did verified independently")
    try:
        data = json.loads(args.fixture.read_text(encoding="utf-8")) if args.fixture else read_profile()
        snapshot = normalize_profile(data, expected_did=args.expected_did)
        if args.output:
            if snapshot["status"] != "ok":
                raise ValueError("Follower count unavailable; preserve last-good snapshot")
            write_json_atomic(args.output, snapshot)
        else:
            print(json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, OSError, HTTPError, URLError, json.JSONDecodeError) as exc:
        print(f"Bluesky snapshot not updated: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
