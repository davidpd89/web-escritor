#!/usr/bin/env python3
"""K.3 regression: the global header affiliate CTA must carry an accessible
'afiliado' disclosure (aria-label), must NOT show a visible label next to
the button, and must point at the site's current canonical purchase URL
(editorial-facts.json's single source of truth) on every page, including
Las manecillas del recuerdo's own pages.

Changed 2026-09-01 (author decision: "que el botón salga COMPRAR y debajo
afiliado, no" -- no visible text under any buy CTA). The disclosure moved
from a visible span next to every CTA to aria-label only (screen readers
still get it) plus the required sitewide Amazon Associates statement in
aviso-legal.html. scripts/build-site-shell.py stamps the same
<a class="header-buy"> Amazon Associates link into the shared header of
every V1 page, so this checks both halves of that contract sitewide, not
just documented as done.

Changed again 2026-09-04: this test used to assert the OPPOSITE of what it
asserts now -- that /las-manecillas-del-recuerdo/'s own pages must NOT show
the header-buy button, because it hardcoded Samuel's Amazon link and
showing it there would have been a bait-and-switch (advertise "Comprar" on
Manecillas' own page while silently selling a different book). Now that
Las manecillas del recuerdo has a real, verified Kindle purchase URL
(editorial-facts.json books.lasManecillasDelRecuerdo.purchaseUrl) and
scripts/build-site-shell.py's PRIMARY_BUY_URL reads it live from there
instead of hardcoding Samuel's link, that exception is gone: the button
must now appear everywhere, including on Manecillas' own pages, and must
point at Manecillas' purchase URL specifically (not Samuel's).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FACTS = json.loads((ROOT / "editorial-facts.json").read_text(encoding="utf-8"))
PRIMARY_BUY_URL = FACTS["books"]["lasManecillasDelRecuerdo"]["purchaseUrl"]
SAMUEL_URL = FACTS["books"]["samuelEntreMundos"]["purchaseUrls"]["amazonEs"]
assert PRIMARY_BUY_URL, "editorial-facts.json: lasManecillasDelRecuerdo.purchaseUrl is unset -- fixture assumption is stale"

EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    ".claude",
    "assets",
    "images",
    "videos",
    "android",
    "tests",
    "_tools",
    "_reddit",
    "_david",
    "WEB DAVID PORTO nuevas ideas",
    "press-kit",
    "data",
    ".preview-dist",
    "dist",
}


def should_skip_file(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    lower = path.name.lower()
    if lower in {"offline.html", "404.html"}:
        return True
    if lower.endswith((".example.html", ".template.html", ".component.html")):
        return True
    return False


HEADER_BUY_RE = re.compile(r'<a class="header-buy"[^>]*>.*?</a>', re.S)

pages_with_header_buy: list[Path] = []
wrong_target_offenders: list[str] = []
disclosure_offenders: list[str] = []

for path in sorted(ROOT.rglob("*.html")):
    if should_skip_file(path):
        continue
    html = path.read_text(encoding="utf-8", errors="ignore")
    if 'class="site-header"' not in html:
        continue  # not a V1-shell page

    match = HEADER_BUY_RE.search(html)
    rel = str(path.relative_to(ROOT))

    if not match:
        # Some V1 fixtures/shells legitimately have no header-buy; only
        # pages that DO carry one are in scope for the checks below.
        continue

    pages_with_header_buy.append(path)
    block = match.group(0)

    href_match = re.search(r'href="([^"]*)"', block)
    href = href_match.group(1) if href_match else ""
    if href != PRIMARY_BUY_URL:
        wrong_target_offenders.append(f"{rel} (href={href!r})")

    has_visible_span = bool(re.search(r'header-buy__disclosure[^>]*>\s*\S', block))
    has_aria = "afiliado" in (re.search(r'aria-label="([^"]*)"', block).group(1).lower()
                               if re.search(r'aria-label="([^"]*)"', block) else "")
    if has_visible_span or not has_aria:
        disclosure_offenders.append(rel)

assert pages_with_header_buy, "no V1 page with a header-buy affiliate link was found -- test fixture assumption is stale"

assert not wrong_target_offenders, (
    f"header-buy must point at the canonical purchase URL ({PRIMARY_BUY_URL}) on every page, "
    "including Las manecillas del recuerdo's own pages: " + ", ".join(wrong_target_offenders)
)

assert not any(SAMUEL_URL in offender for offender in wrong_target_offenders), (
    "header-buy must not silently fall back to Samuel's Amazon link now that Manecillas has its own"
)

assert not disclosure_offenders, (
    "header-buy affiliate link must have an aria-label 'afiliado' disclosure and no visible "
    "header-buy__disclosure span: " + ", ".join(disclosure_offenders)
)

print(f"header-buy-disclosure: OK ({len(pages_with_header_buy)} pages checked, all pointing at {PRIMARY_BUY_URL})")
