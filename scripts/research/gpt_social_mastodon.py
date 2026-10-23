#!/usr/bin/env python3
"""Read-only Mastodon account metrics from a public API, without credentials.

Inspect: python scripts/research/gpt_social_mastodon.py
Publish only after independent account-ID verification:
  python scripts/research/gpt_social_mastodon.py --expected-id VERIFIED_ID --output /tmp/mastodon.json
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
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

HOST = "mastodon.social"
USERNAME = "davidportodiaz"
PROFILE_URL = f"https://{HOST}/@{USERNAME}"
SEARCH_API = f"https://{HOST}/api/v2/search"
MAX_BYTES = 256_000


def request_public_search(*, timeout: float = 10.0) -> dict:
    """Search without resolve/offset, which require a user token."""
    url = SEARCH_API + "?" + urlencode({"q": USERNAME, "type": "accounts", "limit": 5})
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "web-escritor-social-stats/1.0"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Mastodon response too large")
    result = json.loads(body)
    if not isinstance(result, dict):
        raise ValueError("Mastodon response must be an object")
    return result


def is_exact_account(account: dict) -> bool:
    if not isinstance(account, dict):
        return False
    username, acct = account.get("username"), account.get("acct")
    if not isinstance(username, str) or not isinstance(acct, str):
        return False
    if username.casefold() != USERNAME or acct.casefold() != USERNAME:
        return False
    url = account.get("url")
    if not isinstance(url, str):
        return False
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.netloc == HOST
            and parsed.path.rstrip("/").casefold() == f"/@{USERNAME}"
            and not parsed.query and not parsed.fragment)


def count_or_none(value: object) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise ValueError("Mastodon count must be a nonnegative integer or null")
    return value


def normalize_search(data: dict, *, expected_id: str | None = None, observed_at: str | None = None) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("accounts"), list):
        raise ValueError("Mastodon search.accounts must be an array")
    accounts = [a for a in data["accounts"] if is_exact_account(a)]
    if len(accounts) != 1:
        raise ValueError("Expected exactly one canonical Mastodon account")
    account = accounts[0]
    account_id = account.get("id")
    if not isinstance(account_id, str) or not account_id:
        raise ValueError("Mastodon account id missing")
    if expected_id is not None and account_id != expected_id:
        raise ValueError("Mastodon account id changed: stop and verify ownership")
    followers = count_or_none(account.get("followers_count"))
    posts = count_or_none(account.get("statuses_count"))
    return {
        "id": "mastodon", "profile_url": PROFILE_URL, "account_id": account_id,
        "followers": followers, "posts": posts, "views_30d": None,
        "impressions_30d": None, "interactions_30d": None,
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "mastodon-public-search", "status": "ok" if followers is not None else "partial",
    }


def atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".mastodon-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            json.dump(data, output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-id", help="Previously verified Mastodon local account id")
    parser.add_argument("--output", type=Path, help="Explicit output, never a combined social-metrics file")
    parser.add_argument("--fixture", type=Path, help="Read synthetic search response offline; never writes output")
    args = parser.parse_args(argv)
    if args.fixture and args.output:
        parser.error("--fixture cannot be used with --output")
    if args.output and not args.expected_id:
        parser.error("--output requires --expected-id verified independently")
    try:
        data = json.loads(args.fixture.read_text(encoding="utf-8")) if args.fixture else request_public_search()
        snapshot = normalize_search(data, expected_id=args.expected_id)
        if args.output:
            if snapshot["status"] != "ok":
                raise ValueError("Missing followers: preserve last-good snapshot")
            atomic_write(args.output, snapshot)
        else:
            print(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, HTTPError, URLError) as exc:
        print(f"Mastodon snapshot not updated: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
