#!/usr/bin/env python3
"""Regression fixtures for the 1024-byte HTML encoding declaration boundary.

This script is authored for future CI; a [skip ci] draft PR defers execution.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-public-text-encoding.py"
META = b'<meta charset="utf-8">'

# The 1024 limit counts bytes, not Unicode code points.
GOOD = {
    "normal early charset": b"<!doctype html><head>" + META + b"</head>",
    "unquoted charset": b"<meta charset=utf-8>",
    "case-insensitive meta": b"<META CHARSET='UTF-8'>",
    "ends at exactly byte 1024": b" " * (1024 - len(META)) + META,
}
BAD = {
    "declaration completes at byte 1025": b" " * (1025 - len(META)) + META,
    "meta after multibyte content": b"<head>" + ("é" * 600).encode("utf-8") + META,
    "comment containing fake meta": b"<!-- " + META + b" -->",
    "script containing fake meta": b"<script>" + META + b"</script>",
    "wrong charset alias": b'<meta charset="utf-8-preview">',
    "no declaration": b"<!doctype html><html><head></head></html>",
    "invalid UTF-8 despite early charset": b"\xff" + META,
}


def audit_fixture(payload: bytes) -> tuple[int, str]:
    with tempfile.TemporaryDirectory(prefix="public-encoding-") as folder:
        root = Path(folder)
        (root / "scripts").mkdir()
        (root / "data").mkdir()
        shutil.copyfile(CHECKER, root / "scripts" / CHECKER.name)
        (root / "data" / "content-registry.json").write_text(
            json.dumps(
                {"defaults": {}, "entries": [{"status": "public", "sourceFile": "index.html"}]}
            ),
            encoding="utf-8",
        )
        (root / "index.html").write_bytes(payload)
        result = subprocess.run(
            [sys.executable, str(root / "scripts" / CHECKER.name)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout + result.stderr


def main() -> int:
    errors: list[str] = []
    for label, markup in GOOD.items():
        status, output = audit_fixture(markup)
        if status != 0:
            errors.append(f"{label}: unexpected failure: {output}")
    for label, markup in BAD.items():
        status, output = audit_fixture(markup)
        if status == 0:
            errors.append(f"{label}: invalid content was accepted: {output}")
    if errors:
        print("FAIL: public charset first-kilobyte contract")
        for error in errors:
            print(" -", error)
        return 1
    print(f"PASS: first-kilobyte charset contract: {len(GOOD)} valid + {len(BAD)} invalid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
