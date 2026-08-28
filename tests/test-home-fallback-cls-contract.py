#!/usr/bin/env python3
"""Guards the home page no-JS-fallback CLS fix (post-#145 Lighthouse CI).

Root cause: index.html ships a static pre-JS fallback (.river-grid,
.promo-band, #faq, #newsletter -- the old homepage layout) so the page still
works with JS disabled; assets/v1-home-editorial-v3.js's buildFlow() builds
the current "yale" design and removes the fallback on DOMContentLoaded.
Between first paint and that removal the fallback was genuinely visible (a
real Ctrl+Shift+R flash of the old design, confirmed via screen recording,
not a caching artifact). A first fix hid it with display:none, which
collapsed its layout box to zero height; buildFlow() then inserted the new
design into that previously-empty space, which Lighthouse CI measured as a
0.81 CLS regression against a 0.1 budget. Fixed by hiding it with
visibility:hidden instead, which keeps its layout box (so nothing shifts
into new space) while still fully hiding the stale content from view;
measured CLS with this fix is ~0.002. This test locks in visibility:hidden
so a future "just hide it" edit can't reintroduce display:none here.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"

html = INDEX.read_text(encoding="utf-8")

SELECTOR = (
    'html.v1[data-lrb-home="true"] .river-grid,'
    'html.v1[data-lrb-home="true"] .promo-band,'
    'html.v1[data-lrb-home="true"] #faq,'
    'html.v1[data-lrb-home="true"] #newsletter'
)

hide_rule = re.search(re.escape(SELECTOR) + r"\{([^}]*)\}", html)
assert hide_rule, (
    "index.html is missing the home-page no-JS-fallback hide rule for "
    ".river-grid/.promo-band/#faq/#newsletter -- the pre-JS old design would "
    "flash on every load again"
)
assert "visibility:hidden" in hide_rule.group(1), (
    "the home-page fallback hide rule must use visibility:hidden, not "
    "display:none -- display:none collapses the fallback's layout box to "
    "zero height, so buildFlow() inserting the new design into that "
    "now-empty space registers as a large layout shift (measured 0.81 CLS "
    "vs the 0.1 budget on PR #145's Lighthouse CI run)"
)
assert "display:none" not in hide_rule.group(1), (
    "the home-page fallback hide rule must not use display:none -- see "
    "visibility:hidden requirement above"
)

noscript_match = re.search(r"<noscript>\s*<style>([^<]*)</style>\s*</noscript>", html)
assert noscript_match and SELECTOR in noscript_match.group(0), (
    "index.html is missing the <noscript> override that restores the "
    "fallback for real no-JS visitors"
)
assert "visibility:visible" in noscript_match.group(1), (
    "the <noscript> override must restore visibility:visible to match the "
    "visibility:hidden hide rule (display:revert would no longer be undoing "
    "anything once the hide rule uses visibility)"
)

print("PASS home fallback CLS contract")
