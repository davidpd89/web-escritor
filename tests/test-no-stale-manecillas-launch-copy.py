#!/usr/bin/env python3
"""Sitewide regression for prelaunch/"coming soon" copy about Las manecillas
del recuerdo reappearing after publication.

This exact class of bug has shipped twice now: PR #386 fixed "A partir del
3 de septiembre de 2026 * aviso de lanzamiento" (prensa.html) and "incluida
la informacion de compra cuando existan destinos comerciales verificados"
(the book page's newsletter blurb); this second pass (2026-09-05) found
newsletter-general.js and script.js still promising "te avisare cuando Las
manecillas del recuerdo este disponible" in their post-submit copy. The
book has been published since 2026-09-03 and has a real Kindle purchase
link since 2026-09-04 -- none of these should be able to reappear silently.

Scoped to specific, self-contained phrases (not generic words like
"proximamente", which legitimately describes unrelated things elsewhere on
the site, e.g. an editorial submission window) so this can't false-positive
on unrelated prelaunch copy for something else.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIRS = {
    "node_modules", ".git", ".claude", "assets", "images", "videos",
    "android", "tests", "_tools", "_reddit", "_david",
    "WEB DAVID PORTO nuevas ideas", "press-kit", "data",
    ".preview-dist", "dist", "docs",
}

# Self-contained phrases: each one only makes sense as a claim that the book
# is not yet published/purchasable, which has been false since 2026-09-03
# (paperback) / 2026-09-04 (Kindle purchase link).
STALE_PHRASES = [
    "aviso de lanzamiento",
    "cuando existan destinos comerciales verificados",
    "A partir del 3 de septiembre de 2026",
    "Las manecillas del recuerdo esté disponible",
    "Las manecillas del recuerdo este disponible",  # unaccented JS-string variant
]

# Broader paraphrase guard: any "manecillas ... [uncertain-future verb]"
# within a short window, so a differently-worded regression (not one of the
# exact phrases above) still gets caught.
PARAPHRASE_RE = re.compile(
    r"manecillas del recuerdo.{0,40}(este disponible|esté disponible|estar[aá] disponible|cuando salga|cuando se publique)",
    re.I,
)

SCAN_SUFFIXES = (".html", ".js", ".mjs", ".txt")


def should_skip_file(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    if path.suffix.lower() not in SCAN_SUFFIXES:
        return True
    return False


offenders: list[str] = []

for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or should_skip_file(path):
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = str(path.relative_to(ROOT))
    for phrase in STALE_PHRASES:
        if phrase in text:
            offenders.append(f"{rel}: stale phrase {phrase!r}")
    match = PARAPHRASE_RE.search(text)
    if match:
        offenders.append(f"{rel}: stale prelaunch paraphrase near {match.group(0)!r}")

if offenders:
    print("FAIL - no-stale-manecillas-launch-copy:")
    for o in offenders:
        print(f"- {o}")
    raise SystemExit(1)

print("test-no-stale-manecillas-launch-copy: OK")
