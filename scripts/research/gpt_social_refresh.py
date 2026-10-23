#!/usr/bin/env python3
"""Deterministic (no LLM) refresh runner for the public social statistics snapshot.

    python gpt_social_refresh.py            # one refresh, then exit
    python gpt_social_refresh.py --status   # print status.json
    python gpt_social_refresh.py --publish  # also commit/push the JSON (opt-in)

Single-instance lock, retry with backoff on transient errors, persistent log and
status.json in the state dir (%LOCALAPPDATA%\\web-escritor-social or $SOCIAL_STATE_DIR).
Exit codes: 0 ok/unchanged, 1 failed (last-good snapshot preserved), 2 REAUTH REQUIRED, 3 already running, 4 publication failed (data was collected).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gpt_metricool_mcp as mcp  # noqa: E402
import gpt_social_snapshot as snapshot  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
OUTPUT = REPO / "redes-sociales" / "social-metrics.json"
BLUESKY_DID = "did:plc:i5nwasa74ucmiymxjmh57t7x"  # public identifiers
MASTODON_ID = "117238993380408996"
PUBLISH_REMOTE = "https://github.com/davidpd89/web-escritor.git"
STALE_LOCK_SECONDS = 3600
RETRY_DELAYS = (30, 120, 300)


def log(message: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {message}"
    print(line, flush=True)
    with (mcp.state_dir() / "refresh.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire_lock() -> Path | None:
    path = mcp.state_dir() / "refresh.lock"
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as fh:
                fh.write(str(os.getpid()))
            return path
        except FileExistsError:
            try:
                pid = int(path.read_text() or 0)
                stale = not _pid_alive(pid) or time.time() - path.stat().st_mtime > STALE_LOCK_SECONDS
            except (OSError, ValueError):
                stale = True
            if not stale:
                return None
            path.unlink(missing_ok=True)  # leftover from a crash or reboot
    return None


def write_status(update: dict) -> None:
    path = mcp.state_dir() / "status.json"
    try:
        current = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        current = {}
    current.update(update)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(current, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def networks() -> dict:
    try:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        return {n["id"]: {"status": n["status"], "observed_at": n.get("observed_at")} for n in data["networks"]}
    except (OSError, ValueError, KeyError):
        return {}


def attempt() -> int:
    """One snapshot run; maps ReauthRequired to rc=2 and transient errors to rc=1."""
    try:
        return snapshot.main(["--output", str(OUTPUT), "--metricool-live", "--expected-did", BLUESKY_DID,
                              "--expected-mastodon-id", MASTODON_ID])
    except mcp.ReauthRequired as exc:
        log(f"REAUTH REQUIRED: {exc}")
        return 2


def publish() -> int:
    """Delegate to the isolated data-only publisher (dedicated clone, never this worktree)."""
    import gpt_social_publish as pub
    try:
        result = pub.publish(OUTPUT, mcp.state_dir() / "publish-clone", PUBLISH_REMOTE)
    except pub.PublishError as exc:
        log(f"publish failed: {exc}")
        return 4
    publish.last_result = result
    log(f"publish: {result}")
    return 0


publish.last_result = "none"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--status", action="store_true")
    p.add_argument("--publish", action="store_true")
    p.add_argument("--no-retry", action="store_true")
    args = p.parse_args(argv)
    if args.status:
        print((mcp.state_dir() / "status.json").read_text(encoding="utf-8"))
        return 0
    lock = acquire_lock()
    if lock is None:
        log("another refresh is running; exiting")
        return 3
    try:
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        rc = 1
        for n, delay in enumerate((0,) + (() if args.no_retry else RETRY_DELAYS)):
            if delay:
                log(f"retry {n} in {delay}s")
                time.sleep(delay)
            rc = attempt()
            if rc != 1:  # ok, or reauth (retrying cannot help)
                break
        status = {"last_attempt": started, "last_exit_code": rc, "reauth_required": rc == 2,
                  "networks": networks()}
        if rc in (0, 2):  # 2 = Metricool needs login, but fresh Bluesky/Mastodon data and kept values are valid
            status["last_success"] = started  # collection succeeded
            if args.publish:
                prc = publish()
                status["last_publish_ok"] = prc == 0
                status["last_publish_result"] = publish.last_result if prc == 0 else "failed"
                if prc == 0 and publish.last_result == "published":
                    status["last_publish"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                rc = prc or rc  # publication failure (4) outranks; reauth (2) survives a good publish
                status["last_exit_code"] = rc
        write_status(status)
        log(f"finished rc={rc}")
        return rc
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
