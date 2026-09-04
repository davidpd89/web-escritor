#!/usr/bin/env python3
"""Sitewide consistency for Las manecillas del recuerdo's purchase URL
(2026-09-04, Kindle launch).

editorial-facts.json is the single source of truth for
books.lasManecillasDelRecuerdo.purchaseUrl. This locks in two things that
would otherwise be easy to regress silently:

1. The stale prelaunch phrase ("no purchase URL yet") that used to be
   correct across llms.txt/llms-full.txt/ai/index.html/press-kit must not
   come back on any public surface -- it would directly contradict the now-
   real purchase link.
2. Every place that renders a CTA meant to buy Manecillas specifically
   (the global header button, the book page's own hero action, and the
   Home hero's Comprar action) must point at the exact same URL as
   editorial-facts.json, not a stale or hand-typed copy that can drift.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT / "editorial-facts.json").read_text(encoding="utf-8"))
BOOK = FACTS["books"]["lasManecillasDelRecuerdo"]
PURCHASE_URL = BOOK["purchaseUrl"]
assert PURCHASE_URL, "editorial-facts.json: lasManecillasDelRecuerdo.purchaseUrl is unset -- fixture assumption is stale"

STALE_PHRASES = [
    "Sin URL de compra verificada",
    "no existe todavía una URL de compra",
    "todavía no existe una URL de compra verificada",
]

SURFACES = [
    "llms.txt",
    "llms-full.txt",
    "ai/index.html",
    "press-kit/las-manecillas-del-recuerdo.json",
]

errors: list[str] = []

for rel in SURFACES:
    text = (ROOT / rel).read_text(encoding="utf-8")
    for phrase in STALE_PHRASES:
        if phrase in text:
            errors.append(f"{rel}: stale no-purchase-URL phrase survived launch: {phrase!r}")

# CTAs that specifically mean "buy Las manecillas del recuerdo" must all
# resolve to the exact same canonical URL -- not Samuel's link, not a
# hand-typed duplicate that can drift from editorial-facts.json.
home_js = (ROOT / "assets" / "v1-home-editorial-v3.js").read_text(encoding="utf-8")
manecillas_buy_match = re.search(r"const MANECILLAS_BUY_URL = '([^']+)'", home_js)
assert manecillas_buy_match, "assets/v1-home-editorial-v3.js: MANECILLAS_BUY_URL constant not found"
if manecillas_buy_match.group(1) != PURCHASE_URL:
    errors.append(
        f"assets/v1-home-editorial-v3.js: MANECILLAS_BUY_URL ({manecillas_buy_match.group(1)!r}) "
        f"drifted from editorial-facts.json purchaseUrl ({PURCHASE_URL!r})"
    )

shell_py = (ROOT / "scripts" / "build-site-shell.py").read_text(encoding="utf-8")
assert "PRIMARY_BUY_URL = _EDITORIAL_FACTS" in shell_py, (
    "scripts/build-site-shell.py: PRIMARY_BUY_URL must be read live from editorial-facts.json, "
    "not hardcoded as a separate literal"
)

book_html = (ROOT / "las-manecillas-del-recuerdo" / "index.html").read_text(encoding="utf-8")
hero_match = re.search(r'<div class="book-actions">.*?</div>', book_html, re.S)
assert hero_match, "las-manecillas-del-recuerdo/index.html: .book-actions hero block not found"
if PURCHASE_URL not in hero_match.group(0):
    errors.append(
        "las-manecillas-del-recuerdo/index.html: hero .book-actions does not link the canonical purchase URL"
    )

if errors:
    print("FAIL - manecillas-purchase-url-consistency:")
    for err in errors:
        print(f"- {err}")
    raise SystemExit(1)

print(f"test-manecillas-purchase-url-consistency: OK (canonical URL: {PURCHASE_URL})")
