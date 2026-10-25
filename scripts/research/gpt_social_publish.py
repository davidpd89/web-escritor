#!/usr/bin/env python3
"""Data-only publisher for redes-sociales/social-metrics.json (no LLM, never force-pushes).

Works ONLY in a dedicated automation clone (default: <state dir>/publish-clone), never in the
caller's worktree. Steps: validate source -> fetch -> hard-reset the clone to origin/main ->
decide (cadence) -> copy the single file -> prove the diff is exactly that file -> commit ->
plain `git push`; on a non-fast-forward it refetches and retries once, then fails safely.
Credentials come from the user's git credential manager, never from the repo.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gpt_metricool_mcp as mcp  # noqa: E402

REL = "redes-sociales/social-metrics.json"
BRANCH = "main"
MIN_INTERVAL = timedelta(hours=20)   # at most ~1 public update per day
EXPIRY_MARGIN = timedelta(hours=18)  # republish earlier if the remote data nears expiry
FORBIDDEN = ("brandId", "access_token", "refresh_token", "client_id", "Bearer")
NETWORKS = {"bluesky", "mastodon", "threads", "instagram", "tiktok", "pinterest"}


class PublishError(RuntimeError):
    pass


def _t(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(text: str, now: datetime) -> dict:
    """Refuse to publish anything that is not a well-formed, fresh, private-data-free snapshot."""
    try:
        data = json.loads(text)
        nets = data["networks"]
        ids = [n["id"] for n in nets]
        expiry = _t(data["totals"]["valid_until"])
    except (ValueError, KeyError, TypeError) as exc:
        raise PublishError(f"invalid snapshot: {exc}") from exc
    if sorted(ids) != sorted(NETWORKS):
        raise PublishError("snapshot does not list exactly the six official networks")
    for n in nets:
        if n.get("status") == "ok" and not (type(n.get("followers")) is int
                                            and 0 <= n["followers"] <= 2**53 - 1
                                            and str(n.get("profile_url", "")).startswith("https://")):
            raise PublishError(f"bad data for {n.get('id')}")
    if not any(n.get("status") == "ok" for n in nets):
        raise PublishError("no network with fresh data")
    if expiry <= now:
        raise PublishError("snapshot already expired")
    if any(word in text for word in FORBIDDEN):
        raise PublishError("snapshot contains a forbidden private field")
    return data


def effective(data: dict) -> list:
    """Public values ignoring observation timestamps."""
    return [{k: v for k, v in n.items() if k not in ("observed_at", "valid_until")} for n in data["networks"]]


def git(clone: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(clone), *args], capture_output=True, text=True)
    if check and r.returncode:
        raise PublishError(f"git {args[0]} failed: {r.stderr.strip()[:300]}")
    return r


def ensure_clone(clone: Path, remote: str) -> None:
    if (clone / ".git").exists():
        return
    clone.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "clone", "--quiet", "--branch", BRANCH, "--single-branch", remote, str(clone)],
                       capture_output=True, text=True)
    if r.returncode:
        raise PublishError("clone failed: " + r.stderr.strip()[:300])
    git(clone, "config", "user.name", "social-stats-bot")
    git(clone, "config", "user.email", "social-stats-bot@users.noreply.github.com")


def sync(clone: Path) -> None:
    git(clone, "fetch", "--quiet", "origin", BRANCH)
    git(clone, "checkout", "--quiet", "-B", BRANCH, f"origin/{BRANCH}")
    git(clone, "reset", "--quiet", "--hard", f"origin/{BRANCH}")
    git(clone, "clean", "--quiet", "-fd")


def publish(source: Path, clone: Path, remote: str, now: datetime | None = None,
            force_due: bool = False, before_push=None) -> str:
    """Return 'published', 'noop' or 'not-due'; raise PublishError on anything unsafe."""
    now = now or datetime.now(timezone.utc)
    text = source.read_text(encoding="utf-8")
    new = validate(text, now)
    ensure_clone(clone, remote)
    for attempt in (1, 2):
        sync(clone)
        target = clone / REL
        # Reject symlinks before any read, cadence decision or write.
        # Inspect each component, including dangling symlinks.
        for candidate in (clone / Path(REL).parts[0], target):
            if candidate.is_symlink():
                raise PublishError(f"refusing symbolic link in publication path: {candidate}")
        old_text = target.read_text(encoding="utf-8") if target.exists() else ""
        if old_text == text:
            return "noop"
        due = True
        if old_text:
            try:
                old = json.loads(old_text)
                same = effective(old) == effective(new)
                age = now - _t(old["generated_at"])
                near = _t(old["totals"]["valid_until"]) - now < EXPIRY_MARGIN
                due = force_due or near or (not same and age >= MIN_INTERVAL)
            except (ValueError, KeyError, TypeError):
                due = True
        if not due:
            return "not-due"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="")
        git(clone, "add", "--", REL)
        changed = git(clone, "diff", "--cached", "--name-only").stdout.split()
        if changed != [REL]:
            git(clone, "reset", "--quiet", "--hard", f"origin/{BRANCH}")
            raise PublishError(f"refusing to publish: staged files are {changed}, expected only {REL}")
        git(clone, "commit", "--quiet", "-m", "chore(social): refresh follower snapshot")
        ahead = git(clone, "rev-list", "--count", f"origin/{BRANCH}..HEAD").stdout.strip()
        if ahead != "1":
            raise PublishError(f"refusing to push {ahead} commits, expected exactly 1")
        if before_push and attempt == 1:
            before_push()  # test hook: lets a test move the remote between commit and push
        push = git(clone, "push", "--quiet", "origin", f"HEAD:{BRANCH}", check=False)
        if push.returncode == 0:
            return "published"
        if attempt == 2:
            raise PublishError("push rejected twice (main moved or remote refused): " + push.stderr.strip()[:300])
    raise PublishError("unreachable")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--remote", default="https://github.com/davidpd89/web-escritor.git")
    p.add_argument("--clone", type=Path, default=None)
    p.add_argument("--force-due", action="store_true", help="ignore the daily cadence (still data-only and validated)")
    a = p.parse_args(argv)
    try:
        print(publish(a.source, a.clone or mcp.state_dir() / "publish-clone", a.remote, force_due=a.force_due))
        return 0
    except PublishError as exc:
        print(f"publish refused/failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
