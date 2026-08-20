#!/usr/bin/env python3
"""Check that every page references the site's runtime assets
(script.js, styles.css) with the SAME cache-busting version string, and
that no page loads them completely unversioned.

Why this exists: a real incident (2026-08-20, corrective audit point 6)
had 28 pages still on script.js?v=20260615-stable-1 / styles.css?v=...
(a June version) while script.js/styles.css had changed substantially in
August, including the newsletter contract rewrite — meaning most of the
site was silently serving stale cached JS/CSS to returning visitors via
the service worker. Separately, another ~25 pages loaded
/styles.css with no version query string at all. Neither class of bug
was caught by any existing checker.

This checker has two things it can be pointed at:
  1. The current canonical version, read from CANONICAL_VERSION below
     (kept here instead of a separate config file so there is exactly
     one place to bump it — update this constant AND run this checker
     as part of any release that changes script.js or styles.css).
  2. Every git-tracked HTML file's actual script.js/styles.css
     references.

Usage:
  python scripts/check-asset-versions.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Bump this — and only this — when cutting a new release that changes
# script.js and/or styles.css. Then run this checker; it will list every
# page still on the old version.
CANONICAL_VERSION = "202609-launch-1"

REF_RE = re.compile(r'(script\.js|styles\.css)(\?v=([a-zA-Z0-9_.-]+))?')


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
            if not version:
                errors.append(f"{rel}: {asset} loaded with no ?v= at all")
            elif version != CANONICAL_VERSION:
                errors.append(f"{rel}: {asset}?v={version} (expected ?v={CANONICAL_VERSION})")

    if errors:
        print(f"FAIL — {len(errors)} inconsistent/unversioned asset reference(s) across {scanned} page(s) checked:")
        for e in errors:
            print(f"- {e}")
        return 1

    print(f"OK — {scanned} page(s) checked, all script.js/styles.css references use ?v={CANONICAL_VERSION}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
