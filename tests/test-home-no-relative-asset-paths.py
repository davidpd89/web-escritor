#!/usr/bin/env python3
"""index.html must reference /assets/... with a leading slash, never a bare
relative assets/... path (2026-09 audit, GPT round).

PR #365 fixed 23 relative references on this exact page and claimed full
parity with the rest of the site's absolute-path convention, but two more
survived: the intro video's poster= and one <source srcset=> in the river
grid (confirmed still present against main before this fix). Both resolve
identically to /assets/... today only because index.html happens to live
at the site root -- a silent trap for the next time this markup gets
copied into a non-root page, which is exactly how this codebase's shared
head/shell content usually propagates.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "index.html").read_text(encoding="utf-8")

# Anchored to the four attributes that actually load an asset by URL; a
# bare "assets/" appearing in prose/comments is not a real reference.
matches = re.findall(r'(?:href|src|srcset|poster)="assets/[^"]*"', html)

assert not matches, (
    "index.html has relative assets/... reference(s) instead of /assets/...: "
    + ", ".join(matches)
)

print("test-home-no-relative-asset-paths: OK")
