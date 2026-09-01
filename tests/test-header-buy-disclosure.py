#!/usr/bin/env python3
"""K.3 regression: the global header affiliate CTA must carry a visible
disclosure next to itself, not only the sitewide statement in aviso-legal.html.

scripts/build-site-shell.py stamps the same <a class="header-buy"> Amazon
Associates link into the shared header of every V1 page. Amazon's disclosure
policy requires the notice to be near the link itself, so this checks the
disclosure markup is actually present sitewide, not just documented as done.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIRS = {
    "node_modules",
    ".git",
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
manecillas_offenders: list[str] = []
disclosure_offenders: list[str] = []

for path in sorted(ROOT.rglob("*.html")):
    if should_skip_file(path):
        continue
    html = path.read_text(encoding="utf-8", errors="ignore")
    if 'class="site-header"' not in html:
        continue  # not a V1-shell page

    match = HEADER_BUY_RE.search(html)
    rel = str(path.relative_to(ROOT))

    if rel.startswith("las-manecillas-del-recuerdo" + __import__("os").sep) or rel == "las-manecillas-del-recuerdo.html":
        if match:
            manecillas_offenders.append(rel)
        continue

    if not match:
        # Some V1 fixtures/shells legitimately have no header-buy; only
        # pages that DO carry one are in scope for the disclosure check.
        continue

    pages_with_header_buy.append(path)
    block = match.group(0)
    has_visible_span = bool(re.search(r'header-buy__disclosure[^>]*>\s*\S', block))
    has_aria = "afiliado" in (re.search(r'aria-label="([^"]*)"', block).group(1).lower()
                               if re.search(r'aria-label="([^"]*)"', block) else "")
    if not (has_visible_span and has_aria):
        disclosure_offenders.append(rel)

assert pages_with_header_buy, "no V1 page with a header-buy affiliate link was found -- test fixture assumption is stale"

assert not manecillas_offenders, (
    "las-manecillas-del-recuerdo must not show the Samuel Amazon CTA in its own header: "
    + ", ".join(manecillas_offenders)
)

assert not disclosure_offenders, (
    "header-buy affiliate link is missing a visible + accessible 'afiliado' disclosure on: "
    + ", ".join(disclosure_offenders)
)

print(f"header-buy-disclosure: OK ({len(pages_with_header_buy)} pages checked)")
