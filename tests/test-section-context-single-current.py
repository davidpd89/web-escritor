#!/usr/bin/env python3
"""Guards the buildContextNav() aria-current dedup fix (post-#129 audit).

Real bug found: scoring every link independently let an exact-match link
("El libro") and its own ancestor family-match link ("Obras") both claim
aria-current="page" on the same .section-context. The fix is exact-match-wins
with longest-prefix-wins among family matches; this test protects both the
pre-rendered HTML (concrete exact-match-vs-family-match case: Samuel) and a
family-match-only case (Cuaderno, via recomendaciones/*) plus the JS source
no longer scoring links independently.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LINKS_BLOCK_RE = re.compile(r'<div class="section-context__links">(.*?)</div>', re.S)
ARIA_CURRENT_RE = re.compile(r'aria-current="page"')

tracked = ROOT.joinpath("libros/samuel-entre-mundos/index.html")
checked = []
for rel in (
    "libros/samuel-entre-mundos/index.html",
    "recomendaciones/magia-con-coste/index.html",
    "recomendaciones/portal-fantasy-espanol/index.html",
    "universo/noveris/index.html",
    "clubes-de-lectura/samuel-entre-mundos/index.html",
):
    path = ROOT / rel
    assert path.exists(), f"expected pre-rendered section-context page missing: {rel}"
    html = path.read_text(encoding="utf-8")
    match = LINKS_BLOCK_RE.search(html)
    assert match, f"{rel}: no .section-context__links block found"
    count = len(ARIA_CURRENT_RE.findall(match.group(1)))
    assert count <= 1, (
        f"{rel}: .section-context__links has {count} aria-current=\"page\" links, expected at most 1"
    )
    checked.append((rel, count))

# Samuel is the concrete exact-match-vs-family-match case: /libros/ (family)
# and /libros/samuel-entre-mundos/ (exact) are both real links in that
# context. Assert the survivor is specifically the exact match, not just
# "some" link, so a future edit can't swap in the wrong one and still pass.
samuel_html = (ROOT / "libros/samuel-entre-mundos/index.html").read_text(encoding="utf-8")
samuel_block = LINKS_BLOCK_RE.search(samuel_html).group(1)
assert 'href="/libros/samuel-entre-mundos/" aria-current="page"' in samuel_block, (
    "Samuel's exact-match link (El libro) must be the one marked current"
)
assert 'href="/libros/" aria-current="page"' not in samuel_block, (
    "Samuel's family-match link (Obras) must NOT be marked current once an exact match exists"
)

# Recomendaciones pages are the family-match-only case (no link exactly
# equals /recomendaciones/magia-con-coste/; /recomendaciones/ wins as the
# longest/only matching prefix among the context's links).
for rel in ("recomendaciones/magia-con-coste/index.html", "recomendaciones/portal-fantasy-espanol/index.html"):
    html = (ROOT / rel).read_text(encoding="utf-8")
    block = LINKS_BLOCK_RE.search(html).group(1)
    assert 'href="/recomendaciones/" aria-current="page"' in block, (
        f"{rel}: family-match link (Recomendaciones) should be the current one"
    )

# universo/noveris/ and clubes-de-lectura/samuel-entre-mundos/ share the same
# 'samuel' context as libros/samuel-entre-mundos/ itself (same links array),
# discovered while fixing #129 to also have the JS-insertion CLS bug even
# though they weren't in the original fix batch. Each is its own exact match.
noveris_html = (ROOT / "universo/noveris/index.html").read_text(encoding="utf-8")
noveris_block = LINKS_BLOCK_RE.search(noveris_html).group(1)
assert 'href="/universo/noveris/" aria-current="page"' in noveris_block, (
    "Noveris's own exact-match link must be the one marked current"
)
assert 'href="/libros/" aria-current="page"' not in noveris_block, (
    "Noveris must not mark the unrelated family link (Obras) current"
)

club_html = (ROOT / "clubes-de-lectura/samuel-entre-mundos/index.html").read_text(encoding="utf-8")
club_block = LINKS_BLOCK_RE.search(club_html).group(1)
assert 'href="/clubes-de-lectura/samuel-entre-mundos/" aria-current="page"' in club_block, (
    "Club de lectura's own exact-match link must be the one marked current"
)

# The JS source must no longer score every link independently -- that
# pattern is exactly what let two links both qualify.
js = (ROOT / "assets" / "v1-editorial-interior-v4.js").read_text(encoding="utf-8")
assert "if (exact || familyCurrent) link.setAttribute" not in js, (
    "buildContextNav() regressed to scoring each link independently for aria-current"
)
assert "exactMatch" in js and "bestFamilyMatch" in js, (
    "buildContextNav() must keep the exact-match-wins / longest-family-match-wins selection"
)

print(f"PASS section-context single aria-current ({len(checked)} pages checked)")
