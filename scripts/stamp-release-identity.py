#!/usr/bin/env python3
"""Stamp a built public artifact with one exact, cache-resistant release identity.

The marker path contains the full 40-hex Git commit SHA:

    <out>/_release/<sha>.json

This lets post-deploy verification distinguish "the site responds" from "the
specific commit that triggered this deploy is actually being served". An older
release cannot satisfy a request for a marker path it never contained.

This script is intentionally narrow. It only writes the one generated marker
inside an already-built artifact; it never edits source files or deploys.
"""
from __future__ import annotations

import argparse
import json
import re
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
    args = parser.parse_args()

    path = verify(args.out, args.sha) if args.check else stamp(args.out, args.sha)
    action = "VERIFIED" if args.check else "STAMPED"
    print(f"{action} release identity: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
