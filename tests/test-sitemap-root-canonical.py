#!/usr/bin/env python3
"""Regression: the sitemap root must equal the published homepage canonical."""
from __future__ import annotations

import importlib.util
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build-sitemap.py"
EXPECTED = "https://davidportodiaz.com/"
BARE = "https://davidportodiaz.com"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


class CanonicalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        attributes = dict(attrs)
        rel_tokens = (attributes.get("rel") or "").lower().split()
        if "canonical" in rel_tokens:
            self.values.append(attributes.get("href"))


def main() -> None:
    errors: list[str] = []

    parser = CanonicalParser()
    parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
    parser.close()
    if parser.values != [EXPECTED]:
        errors.append(
            f"index.html canonical must be exactly {EXPECTED!r}; got {parser.values!r}"
        )

    spec = importlib.util.spec_from_file_location("build_sitemap", SCRIPT)
    assert spec is not None and spec.loader is not None
    sitemap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sitemap)

    normalized = sitemap.normalize_canonical(EXPECTED, ROOT, ROOT / "index.html")
    if normalized != EXPECTED:
        errors.append(
            f"normalize_canonical changed homepage: {EXPECTED!r} -> {normalized!r}"
        )

    xml_root = ET.parse(ROOT / "sitemap.xml").getroot()
    locations = [element.text for element in xml_root.findall(f".//{{{NS}}}loc")]
    count = locations.count(EXPECTED)
    if count != 1:
        errors.append(
            f"sitemap.xml must contain {EXPECTED!r} exactly once; found {count}"
        )
    if BARE in locations:
        errors.append(f"sitemap.xml contains noncanonical homepage {BARE!r}")

    assert not errors, "\n".join(errors)
    print("PASS sitemap root canonical: HTML, generator and XML agree")


if __name__ == "__main__":
    main()
