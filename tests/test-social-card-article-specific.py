#!/usr/bin/env python3
"""Protect the deliberate social-card choice on key editorial article pages.

The sitewide social-card auditor already validates presence, HTTPS, local asset
existence and real image dimensions. This regression test adds the contract
specific to PR #26: these seven pages must keep the selected thematic editorial
card in both Open Graph and Twitter metadata, with the expected 1200x630
metadata, rather than merely avoiding one known generic URL.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CARD = "https://davidportodiaz.com/assets/og-worldbuilding-noveris-ciudad-fantastica.jpg"
EXPECTED_WIDTH = "1200"
EXPECTED_HEIGHT = "630"
TARGETS = [
    "cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html",
    "cuaderno/libros-fantasia-juvenil-espanola-2025-2026/index.html",
    "cuaderno/portal-fantasy-vs-fantasia-epica/index.html",
    "cuaderno/que-es-el-portal-fantasy/index.html",
    "cuaderno/sistema-de-magia-noveris/index.html",
    "recomendaciones/magia-con-coste/index.html",
    "recomendaciones/portal-fantasy-espanol/index.html",
]


class HeadMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.in_head = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        data = {key.lower(): (value or "") for key, value in attrs}
        if tag == "head":
            self.in_head = True
            return
        if tag == "body":
            self.in_head = False
            return
        if tag != "meta" or not self.in_head:
            return
        key = (data.get("property") or data.get("name") or "").strip().lower()
        if key and key not in self.meta:
            self.meta[key] = data.get("content", "").strip()


errors: list[str] = []

for rel in TARGETS:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"{rel}: target page is missing")
        continue

    parser = HeadMetaParser()
    parser.feed(path.read_text(encoding="utf-8"))
    expected = {
        "og:image": EXPECTED_CARD,
        "twitter:image": EXPECTED_CARD,
        "og:image:width": EXPECTED_WIDTH,
        "og:image:height": EXPECTED_HEIGHT,
    }
    for key, value in expected.items():
        actual = parser.meta.get(key)
        if actual != value:
            errors.append(f"{rel}: {key} is {actual!r}, expected {value!r}")

if errors:
    print("test-social-card-article-specific: FAIL")
    for item in errors:
        print("  -", item)
    raise SystemExit(1)

print(f"test-social-card-article-specific: OK ({len(TARGETS)} pages checked)")
