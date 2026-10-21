#!/usr/bin/env python3
"""OFFLINE Planeta de Libros discovery/edition prototype.

Verifies official listing links and extracts structured candidate fields from a
previously saved HTML document. No HTTP calls, no publication or new cron.
The upstream HTML structure has NOT been validated with raw captured markup:
this is a parser for offline compatibility QA, NOT a live source connector.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT_HOST = "www.planetadelibros.com"
BOOK_PATH = re.compile(r"^/libro-[^/?#]+/[0-9]{3,12}/?$", re.I)
ISBN_TEXT = re.compile(r"\b(97[89](?:[- ]?[0-9]){10})\b")
MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9,
    "octubre": 10, "noviembre": 11, "diciembre": 12,
}
DATE = re.compile(r"\b([0-3]?[0-9])\s+(?:de\s+)?(" + "|".join(MONTHS) +
                  r")\s+(?:de\s+)?(20[0-9]{2})\b", re.I)
MAX_HTML_BYTES = 3 * 1024 * 1024


def product_url(url: object) -> str | None:
    if not isinstance(url, str):
        return None
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != ROOT_HOST or parts.username or parts.password:
        return None
    if parts.query or parts.fragment or not BOOK_PATH.fullmatch(parts.path):
        return None
    return "https://" + ROOT_HOST + parts.path.rstrip("/")


def valid_isbn(value: str) -> str | None:
    digits = re.sub(r"[- ]", "", value)
    if not re.fullmatch(r"97[89][0-9]{10}", digits):
        return None
    expected = (10 - sum(int(n) * (1 if i % 2 == 0 else 3)
                         for i, n in enumerate(digits[:12])) % 10) % 10
    return digits if expected == int(digits[-1]) else None


class ReadHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.in_h1 = 0
        self.h1_parts: list[str] = []
        self.visible: list[str] = []
        self.links: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1
        if tag == "h1":
            self.in_h1 += 1
        if tag == "a" and a.get("href"):
            self.links.add(str(a["href"]))

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_h1 = max(0, self.in_h1 - 1)
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if self.skip:
            return
        text = " ".join(data.split())
        if text:
            self.visible.append(text)
            if self.in_h1:
                self.h1_parts.append(text)


def listing_urls(markup: str) -> list[str]:
    view = ReadHTML()
    view.feed(markup)
    urls = set()
    for href in view.links:
        absolute = urljoin("https://" + ROOT_HOST + "/", href)
        normal = product_url(absolute)
        if normal:
            urls.add(normal)
    return sorted(urls)


def scan_date(text: str) -> str | None:
    found = DATE.search(text)
    if not found:
        return None
    try:
        return date(int(found.group(3)), MONTHS[found.group(2).lower()],
                    int(found.group(1))).isoformat()
    except ValueError:
        return None


def edition_candidate(markup: str, source_url: str) -> dict | None:
    canonical = product_url(source_url)
    if not canonical:
        raise ValueError("Solo páginas de producto Planeta verificadas")
    view = ReadHTML()
    view.feed(markup)
    title = " ".join(view.h1_parts).strip()
    text = " ".join(view.visible)
    index = text.find("Ficha Técnica")
    if not title or index < 0:
        return None
    body = text[index:index + 6000]
    # Require this official edition table's ISBN and exact date.
    raw_isbn = re.search(r"\bISBN\s+" + ISBN_TEXT.pattern, body, re.I)
    isbn = valid_isbn(raw_isbn.group(1)) if raw_isbn else None
    published = re.search(r"\bPublicación\s+(.{0,65})", body, re.I)
    day = scan_date(published.group(1)) if published else None
    publisher = re.search(
        r"\bEditorial\s+(.{2,110}?)\s+(?:ISBN|Páginas|Código|Encuadernación)\b",
        body, re.I,
    )
    page_count = re.search(r"\bPáginas\s+([0-9]{1,4})\b", body, re.I)
    if not isbn or not day or not publisher:
        return None  # Explicitly fail closed instead of guessing.
    return {
        "status": "candidate_review",
        "provider": "planeta",
        "provider_url": canonical,
        "isbn13": isbn, "titulo": title,
        "fecha_publicacion_edicion": day, "precision_fecha": "dia",
        "editorial": " ".join(publisher.group(1).split()),
        "numero_paginas": int(page_count.group(1)) if page_count else None,
        "authors_verified": False, "cover_verified": False, "synopsis_verified": False,
        "note": "Candidato de metadata; falta confirmar autor, cubierta y sinopsis en página original",
    }


def read_html(path: Path) -> str:
    if path.stat().st_size > MAX_HTML_BYTES:
        raise ValueError("HTML de más de 3 MiB; excluir para preview")
    return path.read_text(encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--html", required=True, type=Path)
    p.add_argument("--source-url", help="URL real de ficha, no de índice")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        p.error("No sobrescribir resultados previos")
    markup = read_html(args.html)
    if args.source_url:
        row = edition_candidate(markup, args.source_url)
        data = {"schema_version": 1, "provider": "planeta",
                "candidates": [row] if row else []}
    else:
        data = {"schema_version": 1, "provider": "planeta",
                "product_urls": listing_urls(markup)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps({"source": "planeta", "count": len(data.get(
        "candidates", data.get("product_urls", []))), "published": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
