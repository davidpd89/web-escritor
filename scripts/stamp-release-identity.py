#!/usr/bin/env python3
"""Stamp a built public artifact with one exact, cache-resistant release identity.

The marker path contains the full 40-hex Git commit SHA:

    <out>/_release/<sha>.json

This lets post-deploy verification distinguish "the site responds" from "the
specific commit that triggered this deploy is actually being served". An older
release cannot satisfy a request for a marker path it never contained.

R5-13: with `--hoy`, it also writes `<out>/version.json` = {sha, hoy}, the
public answer to "which commit and which Madrid day is live?". A watchdog
(GitHub cron or Worker) compares `hoy` with today's Madrid date and re-triggers
the deploy when the day did not change.

This script is intentionally narrow. It only writes the one generated marker
inside an already-built artifact; it never edits source files or deploys.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def validate_sha(value: str) -> str:
    sha = value.strip().lower()
    if not SHA_RE.fullmatch(sha):
        raise ValueError("release SHA must be exactly 40 hexadecimal characters")
    return sha


def marker_path(out_dir: Path, sha: str) -> Path:
    return out_dir / "_release" / f"{validate_sha(sha)}.json"


def stamp(out_dir: Path, sha: str) -> Path:
    if not out_dir.is_dir():
        raise FileNotFoundError(f"built artifact directory does not exist: {out_dir}")
    normalized = validate_sha(sha)
    path = marker_path(out_dir, normalized)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": 1,
        "sha": normalized,
    }
    path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    return path


def version_payload(sha: str, hoy: str) -> dict:
    return {"schemaVersion": 1, "sha": validate_sha(sha), "hoy": date.fromisoformat(hoy).isoformat()}


def stamp_version(out_dir: Path, sha: str, hoy: str) -> Path:
    path = out_dir / "version.json"
    path.write_text(json.dumps(version_payload(sha, hoy), separators=(",", ":")) + "\n", encoding="utf-8")
    return path


def verify_version(out_dir: Path, sha: str, hoy: str) -> Path:
    path = out_dir / "version.json"
    if json.loads(path.read_text(encoding="utf-8")) != version_payload(sha, hoy):
        raise ValueError(f"version.json content mismatch: {path}")
    return path


def verify(out_dir: Path, sha: str) -> Path:
    normalized = validate_sha(sha)
    path = marker_path(out_dir, normalized)
    if not path.is_file():
        raise FileNotFoundError(f"release marker missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload != {"schemaVersion": 1, "sha": normalized}:
        raise ValueError(f"release marker content mismatch: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="already-built public artifact directory")
    parser.add_argument("--sha", required=True, help="exact 40-hex Git commit SHA")
    parser.add_argument("--check", action="store_true", help="verify marker instead of writing it")
    parser.add_argument("--hoy", help="Madrid day YYYY-MM-DD the artifact was built for (writes /version.json)")
    args = parser.parse_args()

    path = verify(args.out, args.sha) if args.check else stamp(args.out, args.sha)
    action = "VERIFIED" if args.check else "STAMPED"
    print(f"{action} release identity: {path}")
    if args.hoy:
        version = (verify_version if args.check else stamp_version)(args.out, args.sha, args.hoy)
        print(f"{action} version: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
