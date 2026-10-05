#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_HOST = "davidportodiaz.com"
REGISTRY = json.loads((ROOT / "data/content-registry.json").read_text(encoding="utf-8"))
DEFAULTS = REGISTRY.get("defaults", {})

class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[tuple[int, dict[str, str]]] = []

    def handle_starttag(self, tag, attrs):
        data = {k.lower(): (v or "") for k, v in attrs}
        if data.get("id"):
            self.ids.add(data["id"])
        if tag.lower() == "a" and "href" in data:
            self.links.append((self.getpos()[0], data))

def public_html() -> list[Path]:
    out: set[Path] = set()
    for raw in REGISTRY.get("entries", []):
        item = {**DEFAULTS, **raw}
        source = str(item.get("sourceFile") or "")
        if item.get("status") == "public" and source.endswith(".html"):
            path = ROOT / source
            if path.is_file():
                out.add(path)
    for name in ("404.html", "offline.html"):
        p = ROOT / name
        if p.is_file():
            out.add(p)
    return sorted(out)

errors: list[str] = []
checked_links = 0
for path in public_html():
    rel = path.relative_to(ROOT).as_posix()
    parser = Parser()
    parser.feed(path.read_text(encoding="utf-8"))
    for line, attrs in parser.links:
        checked_links += 1
        href = attrs.get("href", "").strip()
        low = href.lower()

        if low.startswith("javascript:"):
            errors.append(f"{rel}:{line}: javascript: href is forbidden")

        if attrs.get("target", "").lower() == "_blank":
            rel_tokens = set(attrs.get("rel", "").lower().split())
            if "noopener" not in rel_tokens:
                errors.append(f"{rel}:{line}: target=_blank without rel=noopener ({href})")

        if href.startswith("#") and len(href) > 1:
            fragment = href[1:]
            if fragment not in parser.ids:
                errors.append(f"{rel}:{line}: fragment #{fragment} has no target id")

        try:
            u = urlsplit(href)
        except ValueError:
            errors.append(f"{rel}:{line}: malformed href {href!r}")
            continue
        host = (u.hostname or "").lower()
        if host in {CANONICAL_HOST, "www." + CANONICAL_HOST}:
            if u.scheme.lower() != "https" or host != CANONICAL_HOST:
                errors.append(f"{rel}:{line}: non-canonical internal absolute URL {href}")

if errors:
    print(f"PUBLIC LINK SEMANTICS: FAIL ({len(errors)} issue(s))")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print(f"PUBLIC LINK SEMANTICS: PASS ({len(public_html())} public HTML files, {checked_links} links)")
