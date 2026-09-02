#!/usr/bin/env python3
"""Check that every page references the site's runtime assets
with the SAME cache-busting version string per asset, and that no page
loads a tracked asset completely unversioned.

Why this exists: a real incident (2026-08-20, corrective audit point 6)
had 28 pages still on script.js?v=20260615-stable-1 / styles.css?v=...
(a June version) while script.js/styles.css had changed substantially in
August, including the newsletter contract rewrite — meaning most of the
site was silently serving stale cached JS/CSS to returning visitors via
the service worker. Separately, another ~25 pages loaded
/styles.css with no version query string at all. Neither class of bug
was caught by any existing checker.

A second incident (2026-09-02) hit the exact same class of bug on two
different assets this checker didn't cover yet: v1-fonts.css was loaded
completely unversioned on 71 pages, and v1-home.css?v=9 on index.html
was never bumped across two rounds of real fixes to that file (a font-
display change, then a corner-bracket/divider fix) -- so the author kept
seeing the pre-fix behavior on every reload. Added both to TRACKED_ASSETS
below rather than creating a second, separate checker for them.

This checker has two things it can be pointed at:
  1. The current canonical version per asset, read from TRACKED_ASSETS
     below (kept here instead of a separate config file so there is
     exactly one place to bump each — update the relevant entry AND run
     this checker as part of any release that changes that asset).
  2. Every git-tracked HTML file's actual references to each asset.

Usage:
  python scripts/check-asset-versions.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Bump the relevant entry — and only that entry — when cutting a release
# that changes the given asset. Then run this checker; it will list every
# page still on the old version, or still completely unversioned.
TRACKED_ASSETS = {
    "script.js": "202609-launch-1",
    "styles.css": "202609-launch-1",
    "v1-fonts.css": "1",
    "v1-home.css": "10",
}

REF_RE = re.compile(r'(' + '|'.join(re.escape(a) for a in TRACKED_ASSETS) + r')(\?v=([a-zA-Z0-9_.-]+))?')


def git_tracked_html():
    result = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            yield ROOT / line


def main() -> int:
    errors = []
    scanned = 0
    for path in git_tracked_html():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        rel = path.relative_to(ROOT)
        matches = REF_RE.findall(text)
        if not matches:
            continue
        scanned += 1
        for asset, _qs, version in matches:
            canonical = TRACKED_ASSETS[asset]
            if not version:
                errors.append(f"{rel}: {asset} loaded with no ?v= at all")
            elif version != canonical:
                errors.append(f"{rel}: {asset}?v={version} (expected ?v={canonical})")

    if errors:
        print(f"FAIL — {len(errors)} inconsistent/unversioned asset reference(s) across {scanned} page(s) checked:")
        for e in errors:
            print(f"- {e}")
        return 1

    versions = ", ".join(f"{a}?v={v}" for a, v in TRACKED_ASSETS.items())
    print(f"OK — {scanned} page(s) checked, all tracked asset references match ({versions}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
