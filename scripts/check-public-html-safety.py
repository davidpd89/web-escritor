#!/usr/bin/env python3
"""Global safety contract for public HTML.

Checks every indexable HTML route from sitemap.xml plus deliberately public
HTML pages that are not indexed. It guards invariants that should never vary
by template or section.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXTRA_PUBLIC_HTML = ("404.html", "offline.html", "privacidad.html", "aviso-legal.html")
URL_ATTRS = ("href", "src", "action", "formaction", "poster")

SRCSET_ATTRS = ("srcset", "imagesrcset")
ASCII_WS = " \\t\\n\\r\\f"


def srcset_urls(value: str):
    """Yield candidate URLs using the WHATWG srcset token-boundary rules.

    A comma may be part of a URL (notably data: URLs); it is a separator
    only after a URL token or a descriptor. Never split srcset on commas.
    """
    pos = 0
    size = len(value)
    while pos < size:
        while pos < size and (value[pos] in ASCII_WS or value[pos] == ","):
            pos += 1
        if pos >= size:
            break
        start = pos
        while pos < size and value[pos] not in ASCII_WS:
            pos += 1
        token = value[start:pos]
        url = token.rstrip(",")
        if url:
            yield url
        if token.endswith(","):
            continue

        # Consume optional descriptors (1x, 480w, etc.) until a separator.
        # Parentheses inside a descriptor must not split a candidate.
        in_parens = False
        while pos < size:
            ch = value[pos]
            pos += 1
            if ch == "(":
                in_parens = True
            elif ch == ")":
                in_parens = False
            elif ch == "," and not in_parens:
                break



def route_to_file(url: str) -> Path:
    path = urlparse(url).path
    if path in {"", "/"}:
        return ROOT / "index.html"
    rel = path.lstrip("/")
    if path.endswith("/"):
        rel += "index.html"
    return ROOT / rel


class AuditParser(HTMLParser):
    def __init__(self, rel: str):
        super().__init__(convert_charrefs=True)
        self.rel = rel
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        self._check(tag, attrs)

    def handle_startendtag(self, tag: str, attrs):
        self._check(tag, attrs)

    def _check(self, tag: str, attrs):
        data: dict[str, list[str]] = {}
        for key, value in attrs:
            data.setdefault(str(key).lower(), []).append("" if value is None else str(value))
        tag = tag.lower()

        if tag == "a" and any(v.lower() == "_blank" for v in data.get("target", [])):
            rel_tokens = {token.lower() for value in data.get("rel", []) for token in value.split()}
            if "noopener" not in rel_tokens:
                self.errors.append(f'{self.rel}: target="_blank" link without rel="noopener"')

        if tag == "img" and "alt" not in data:
            self.errors.append(f"{self.rel}: <img> without alt attribute")

        if tag == "iframe" and not any(v.strip() for v in data.get("title", [])):
            self.errors.append(f"{self.rel}: <iframe> without non-empty title")

        for attr in URL_ATTRS:
            for raw in data.get(attr, []):
                self._check_url(attr, raw)
        for attr in SRCSET_ATTRS:
            for raw in data.get(attr, []):
                for candidate in srcset_urls(raw):
                    self._check_url(attr, candidate)

        if tag == "meta" and any(v.lower() == "refresh" for v in data.get("http-equiv", [])):
            for value in data.get("content", []):
                marker = value.lower().find("url=")
                if marker >= 0:
                    target = value[marker + 4:].strip(" \t'\"")
                    if target.startswith("//") or target.lower().startswith(("http://", "javascript:")):
                        self.errors.append(f"{self.rel}: unsafe meta refresh target {target}")


    def _check_url(self, attr: str, raw: str):
        value = raw.strip()
        low = value.lower()
        if low.startswith("javascript:"):
            self.errors.append(f"{self.rel}: {attr} uses javascript: URL")
        elif value.startswith("//"):
            self.errors.append(f"{self.rel}: {attr} uses protocol-relative URL {value}")
        elif low.startswith("http://"):
            host = (urlparse(value).hostname or "").lower()
            if host not in {"www.w3.org", "w3.org"}:
                self.errors.append(f"{self.rel}: mixed-content {attr} {value}")



def main() -> int:
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [n.text.strip() for n in root.findall(".//sm:loc", ns) if n.text and n.text.strip()]
    files: list[Path] = []
    seen: set[Path] = set()
    errors: list[str] = []

    for url in urls:
        path = route_to_file(url)
        if not path.exists():
            errors.append(f"sitemap URL has no local file: {url} -> {path.relative_to(ROOT)}")
            continue
        if path.suffix.lower() != ".html":
            errors.append(f"sitemap URL does not resolve to HTML: {url} -> {path.relative_to(ROOT)}")
            continue
        if path not in seen:
            seen.add(path)
            files.append(path)

    for rel in EXTRA_PUBLIC_HTML:
        path = ROOT / rel
        if path.exists() and path not in seen:
            seen.add(path)
            files.append(path)

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        parser = AuditParser(rel)
        try:
            parser.feed(path.read_text(encoding="utf-8"))
            parser.close()
        except Exception as exc:
            errors.append(f"{rel}: parser failure: {exc}")
            continue
        errors.extend(parser.errors)

    if errors:
        print(f"FAIL public HTML safety: {len(errors)} issue(s) across {len(files)} files")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"PASS public HTML safety: {len(files)} files; "
        "noopener, URL schemes, image alt and iframe titles clean"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
