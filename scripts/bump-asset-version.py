#!/usr/bin/env python3
"""Bump one tracked asset's cache-busting version everywhere at once.

Changing a file under assets/ (or script.js / styles.css) in this repo means
three edits that have to stay in sync, or returning visitors keep being served
the old bytes from the service worker: the ?v= in every page that references
it, the canonical entry in scripts/check-asset-versions.py, and the content
hash in scripts/asset-version-hashes.json. Doing it by hand is how
v1-home.css?v=9 survived two rounds of real fixes in 2026-09 while the author
kept seeing the pre-fix behaviour on every reload.

References live in authored HTML *and* in builder/test sources that emit the
same markup (scripts/build-*.py, qa/*.mjs), so a plain find-and-replace over
*.html is not enough either -- that is what this script walks.

Usage:
    python scripts/bump-asset-version.py v1-shell.js 16
    python scripts/bump-asset-version.py script.js 202610-launch-27

It refuses to run if the asset is not in TRACKED_ASSETS, if the declared
version is already the requested one, or if no reference was found (which
would mean the name is wrong). Afterwards it records the new hash and runs the
checker, so a green run means all three places agree.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-asset-versions.py"
TEXT_EXTS = {".html", ".py", ".js", ".mjs", ".json", ".yml", ".yaml", ".md", ".xml", ".txt", ".css"}
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / line for line in out.stdout.splitlines() if line]


def declared_version(asset: str) -> str | None:
    source = CHECKER.read_text(encoding="utf-8")
    match = re.search(rf'^\s*"{re.escape(asset)}":\s*"([^"]+)",', source, re.MULTILINE)
    return match.group(1) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("asset", help="file name as it appears in TRACKED_ASSETS, e.g. v1-shell.js")
    parser.add_argument("version", help="new version string, e.g. 16")
    args = parser.parse_args()

    if not VERSION_RE.match(args.version):
        print(f"ERROR: version {args.version!r} is not a plain cache-busting token", file=sys.stderr)
        return 2

    old = declared_version(args.asset)
    if old is None:
        print(f"ERROR: {args.asset} is not in TRACKED_ASSETS (scripts/check-asset-versions.py)", file=sys.stderr)
        return 2
    if old == args.version:
        print(f"ERROR: {args.asset} is already declared at ?v={old}", file=sys.stderr)
        return 2

    old_ref = f"{args.asset}?v={old}".encode()
    new_ref = f"{args.asset}?v={args.version}".encode()
    # A trailing digit boundary so bumping ?v=1 never rewrites ?v=12.
    pattern = re.compile(re.escape(old_ref) + rb"(?![0-9A-Za-z._-])")

    changed: list[str] = []
    total = 0
    for path in tracked_files():
        if path.suffix.lower() not in TEXT_EXTS or not path.is_file():
            continue
        # The hash lockfile is owned by the checker, never rewritten textually.
        if path == ROOT / "scripts" / "asset-version-hashes.json":
            continue
        raw = path.read_bytes()
        patched, hits = pattern.subn(new_ref, raw)
        if hits:
            path.write_bytes(patched)
            changed.append(path.relative_to(ROOT).as_posix())
            total += hits

    if not changed:
        print(f"ERROR: no reference to {args.asset}?v={old} found; nothing was written", file=sys.stderr)
        return 1

    source = CHECKER.read_text(encoding="utf-8")
    source, count = re.subn(
        rf'(^\s*"{re.escape(args.asset)}":\s*)"{re.escape(old)}",',
        lambda m: f'{m.group(1)}"{args.version}",',
        source,
        count=1,
        flags=re.MULTILINE,
    )
    assert count == 1, "TRACKED_ASSETS entry vanished between read and write"
    CHECKER.write_text(source, encoding="utf-8", newline="")
    CHECKER.write_bytes(CHECKER.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))

    print(f"{args.asset}: ?v={old} -> ?v={args.version} ({total} reference(s) in {len(changed)} file(s))")
    for step in (["--update-hashes"], []):
        result = subprocess.run([sys.executable, str(CHECKER), *step], cwd=ROOT)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
