#!/usr/bin/env python3
"""Sitewide regression for the 2026-09-01 author decision: affiliate/buy CTAs
must disclose "enlace de afiliado" via aria-label (screen readers) and the
sitewide Amazon Associates statement in aviso-legal.html, never as visible
text next to the link ("que el boton salga COMPRAR y debajo afiliado, no").

tests/test-header-buy-disclosure.py already locks this in for the single
<a class="header-buy"> pattern build-site-shell.py stamps into every header.
This test catches the same regression anywhere else on the site: a hand-
written page can just as easily add a visible "(enlace de afiliado)" or
"<span>-- enlace con afiliacion</span>" next to an ordinary buy link, which
is exactly what reappeared on /ai/ and /las-manecillas-del-recuerdo/kindle/
on 2026-09-04 before this test existed.

JSON-LD (<script type="application/ld+json">) is exempt: it is machine-
readable data, not visible UI, and GPT's own review of this regression
agreed it doesn't count.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIRS = {
    "node_modules", ".git", ".claude", "assets", "images", "videos",
    "android", "tests", "_tools", "_reddit", "_david",
    "WEB DAVID PORTO nuevas ideas", "press-kit", "data",
    ".preview-dist", "dist",
}

# Visible-text pattern: a ">" (end of some tag) immediately followed by an
# em-dash disclosure, or a parenthetical disclosure right after a link's
# closing text -- both are how this regression has actually appeared.
VISIBLE_DISCLOSURE_RE = re.compile(
    r'>\s*[—-]\s*enlace (con afiliaci[oó]n|de afiliado)|\(enlace de afiliado\)',
    re.I,
)
LD_JSON_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>.*?</script>',
    re.I | re.S,
)


def should_skip_file(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    return False


offenders: list[str] = []

for path in sorted(ROOT.rglob("*.html")):
    if should_skip_file(path):
        continue
    html = path.read_text(encoding="utf-8", errors="ignore")
    stripped = LD_JSON_RE.sub("", html)
    if VISIBLE_DISCLOSURE_RE.search(stripped):
        offenders.append(str(path.relative_to(ROOT)))

if offenders:
    print("FAIL - no-visible-affiliate-disclosure:")
    for rel in offenders:
        print(f"- {rel}: visible affiliate disclosure text found outside JSON-LD -- "
              "use aria-label instead (see tests/test-header-buy-disclosure.py)")
    raise SystemExit(1)

print("test-no-visible-affiliate-disclosure: OK")
