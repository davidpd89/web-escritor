#!/usr/bin/env python3
"""Audita enlaces visibles hacia reseñas y seguimiento, sin usar la red.

Uso: python scripts/audit-reader-engagement-links.py
No inicia sesión, no publica reseñas, no crea cuentas y no modifica el sitio.
"""
from __future__ import annotations

import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "autor": "autor.html",
    "samuel": "libros/samuel-entre-mundos/index.html",
    "manecillas": "las-manecillas-del-recuerdo/index.html",
}


def plain(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value).lower().strip()


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.current: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a" or self.current is not None:
            return
        fields = dict(attrs)
        self.current = {
            "href": fields.get("href") or "",
            "text": "",
            "aria": fields.get("aria-label") or "",
        }

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


def analyse_html(html: str) -> dict[str, object]:
    parser = Links()
    parser.feed(html)
    found: dict[str, list[str]] = {
        "amazon_follow": [],
        "amazon_review": [],
        "amazon_review_view": [],
        "amazon_author_profile_view": [],
        "goodreads_review": [],
        "casa_review": [],
    }
    review_amazon_miscounted = []
    amazon_nonpurchase_miscounted = []
    misleading_cross_platform_labels = []
    for link in parser.links:
        href = link["href"]
        parsed = urlsplit(href)
        host = parsed.hostname or ""
        wording = plain(link["text"] + " " + link["aria"])
        # Una etiqueta que anuncia dos plataformas no debe abrir solo una.
        if "amazon" in wording and "goodreads" in wording:
            misleading_cross_platform_labels.append({"href": href, "label": wording})
        direct_review = (
            "dejar resena" in wording
            or "escribir resena" in wording
            or "valorar en" in wording
            or "dejar opinion" in wording
        )
        if host in ("amazon.es", "www.amazon.es"):
            is_author = "/stores/author/" in parsed.path
            is_review_dest = plain(parsed.fragment) == "customerreviews"
            is_review_wording = ("resen" in wording or "opinion" in wording)
            if is_author and "seguir" in wording:
                found["amazon_follow"].append(href)
            elif is_author:
                found["amazon_author_profile_view"].append(href)
            if direct_review:
                found["amazon_review"].append(href)
                review_amazon_miscounted.append(href)
            elif is_review_dest or is_review_wording:
                found["amazon_review_view"].append(href)
            if is_author or direct_review or is_review_dest or is_review_wording:
                amazon_nonpurchase_miscounted.append(href)
        elif host == "www.goodreads.com" and direct_review:
            found["goodreads_review"].append(href)
        elif host == "www.casadellibro.com" and direct_review:
            found["casa_review"].append(href)
    return {
        "ctas": found,
        # script.js en main cuenta TODOS los clics a amazon.es como comprar-amazon,
        # sin distinguir "dejar reseña" de "comprar".
        "amazon_review_links_also_match_purchase_listener": review_amazon_miscounted,
        "amazon_nonpurchase_links_also_match_purchase_listener": amazon_nonpurchase_miscounted,
        "misleading_cross_platform_labels": misleading_cross_platform_labels,
    }


def audit(root: Path = ROOT) -> dict[str, object]:
    pages = {}
    for name, path in PAGES.items():
        pages[name] = analyse_html((root / path).read_text(encoding="utf-8"))
    return {
        "version": "2026-10-22",
        "pages": pages,
        "limitations": (
            "Analiza HTML versionado, no destino externo, ranking, cuenta "
            "de autor, clics reales ni publicación de reseñas."
        ),
    }


def main() -> int:
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
