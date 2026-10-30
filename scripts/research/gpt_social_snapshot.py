#!/usr/bin/env python3
"""One-command offline pipeline: adapters -> compositor -> idempotent public JSON.

python scripts/research/gpt_social_snapshot.py --output out/social-metrics.json \
    --bluesky-fixture tests/fixtures/social/bluesky_profile.fixture.json \
    --mastodon-fixture tests/fixtures/social/mastodon_search.fixture.json \
    --metricool-export tests/fixtures/social/metricool_followers.fixture.json \
    --now 2026-10-22T08:00:00Z

Without --*-fixture, Bluesky and Mastodon are read from their public APIs.
Metricool is always a private local export (no API key here). A failing source
leaves its network pending, or keeps the previous unexpired value; the file is
rewritten only when published content changes (generated_at is ignored).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

import gpt_metricool_followers as metricool
import gpt_metricool_live as metricool_live
import gpt_social_bluesky as bluesky
import gpt_social_compose as compose
import gpt_social_mastodon as mastodon


def load(path: Path) -> object:
    if path.stat().st_size > compose.MAX_INPUT_BYTES:
        raise ValueError("source file too large")
    return json.loads(path.read_text(encoding="utf-8"))


def collect(args: argparse.Namespace, errors: list[str], now: datetime) -> list[dict]:
    stamp = now.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    jobs = {
        "bluesky": lambda: bluesky.normalize_profile(
            load(args.bluesky_fixture) if args.bluesky_fixture else bluesky.read_profile(),
            expected_did=args.expected_did, observed_at=stamp),
        "mastodon": lambda: mastodon.normalize_search(
            load(args.mastodon_fixture) if args.mastodon_fixture else mastodon.request_public_search(),
            expected_id=args.expected_mastodon_id, observed_at=stamp),
    }
    if args.metricool_export:
        jobs["metricool"] = lambda: metricool.normalize(load(args.metricool_export))
    elif args.metricool_live:
        jobs["metricool"] = lambda: metricool_live.read(now)
    sources = []
    for name, job in jobs.items():
        try:
            sources.append(job())
        except metricool_live.mcp.ReauthRequired as exc:
            args.reauth_required = True  # keep the other sources and the last-good Metricool values
            errors.append(f"{name}: REAUTH REQUIRED: {exc}")
        except Exception as exc:  # one failing source must not block the others
            errors.append(f"{name}: {exc}")
    return sources


def carry_over(previous: object, sources: list[dict], now: datetime) -> list[dict]:
    """Re-validate unexpired last-good records for networks whose source failed."""
    if not isinstance(previous, dict) or not isinstance(previous.get("networks"), list):
        return []
    have = {r["id"] for s in sources for r in compose.public_records(s)}
    kept = []
    for record in previous["networks"]:
        if not isinstance(record, dict) or record.get("id") in have or record.get("followers") is None:
            continue
        try:
            _, ok = compose.normalize({k: record[k] for k in ("id", "source", "status", "followers", "observed_at")}, now)
        except (KeyError, ValueError):
            continue
        if ok["status"] == "ok":
            kept.append(record | {"profile_url": compose.PROFILES.get(record["id"])})
    return kept


def drop_false_zeros(previous: object, sources: list[dict], errors: list[str]) -> list[dict]:
    """Discard a 0 that replaces a positive count: Metricool returns 0 for a day it
    has not consolidated yet, and a real account never loses every follower overnight."""
    if not isinstance(previous, dict) or not isinstance(previous.get("networks"), list):
        return sources
    before = {r.get("id"): r.get("followers") for r in previous["networks"] if isinstance(r, dict)}

    def suspicious(record: object) -> bool:
        if not isinstance(record, dict) or record.get("followers") != 0:
            return False
        last = before.get(record.get("id"))
        if isinstance(last, int) and last > 0:
            errors.append(f"{record.get('id')}: 0 followers after {last}; kept last-good value")
            return True
        return False

    kept = []
    for source in sources:
        if isinstance(source, dict) and source.get("kind") == compose.METRICOOL_BATCH_KIND:
            records = [r for r in source.get("records") or [] if not suspicious(r)]
            if not records:
                continue  # an empty batch is invalid; the last-good values carry over instead
            source = source | {"records": records}
        elif suspicious(source):
            continue
        kept.append(source)
    return kept


REFRESH = timedelta(hours=6)
TIMING = ("generated_at", "observed_at", "valid_until")


def comparable(payload: object) -> object:
    return {k: v for k, v in payload.items() if k != "generated_at"} if isinstance(payload, dict) else payload


def same_content(previous: object, payload: dict, now: datetime) -> bool:
    """True when only observation timestamps moved and the old ones are still recent."""
    if comparable(previous) == comparable(payload):
        return True
    if not isinstance(previous, dict) or not isinstance(previous.get("networks"), list):
        return False

    def core(p: dict) -> list:
        return [{k: v for k, v in n.items() if k not in TIMING} for n in p["networks"]]

    try:
        if core(previous) != core(payload) or previous.get("totals") != payload.get("totals"):
            return False
        moved = [old["observed_at"] for old, new in zip(previous["networks"], payload["networks"])
                 if old.get("observed_at") != new.get("observed_at")]
        return all(timedelta(0) <= now - datetime.fromisoformat(t.replace("Z", "+00:00")) < REFRESH
                   for t in moved)
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--bluesky-fixture", type=Path)
    p.add_argument("--mastodon-fixture", type=Path)
    p.add_argument("--metricool-export", type=Path)
    p.add_argument("--metricool-live", action="store_true",
                   help="read Metricool through the authenticated official MCP (needs the one-time login)")
    p.add_argument("--expected-did")
    p.add_argument("--expected-mastodon-id")
    p.add_argument("--now", help="UTC ISO instant for reproducible runs (default: current time)")
    args = p.parse_args(argv)
    errors: list[str] = []
    try:
        now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
        sources = collect(args, errors, now)
        previous = None
        if args.output.exists():
            try:
                previous = json.loads(args.output.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                previous = None
        sources = drop_false_zeros(previous, sources, errors)
        sources += carry_over(previous, sources, now)
        payload = compose.compose(sources, now=now)
        if not any(n["status"] == "ok" for n in payload["networks"]):
            raise ValueError("no fresh verified follower data; last-good output preserved")
        changed = not same_content(previous, payload, now)
        if changed:
            compose.atomic_write(args.output, payload)
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        print("Social snapshot not updated: " + "; ".join(errors), file=sys.stderr)
        return 1
    for e in errors:
        print(f"warning: {e}", file=sys.stderr)
    print(f"{'written' if changed else 'unchanged'}: {args.output} "
          f"({payload['totals']['coverage']}/{payload['totals']['eligible']} networks)")
    return 2 if getattr(args, "reauth_required", False) else 0  # 2 = data kept, but Metricool needs `login`


if __name__ == "__main__":
    raise SystemExit(main())
