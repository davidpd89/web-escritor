#!/usr/bin/env python3
"""Inventario offline de enlaces Amazon en el sitio y catálogo. Sin red, cookies ni clics.

Uso: python scripts/audit-amazon-links.py [--json] [--root RUTA] [--tag ID]
No demuestra atribución/comisiones: completar con Link Checker e informes Amazon.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED = {".git", ".preview-dist", "node_modules", "artifacts", "tests", "qa", "docs"}
ASIN_RE = re.compile(r"/(?:[^/]+/)?(?:dp|gp/product)/([A-Z0-9]{10})(?:/|$)", re.I)


def html_paths(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "*.html"], cwd=root, check=True,
            capture_output=True, text=True,
        )
        paths = [root / rel for rel in result.stdout.splitlines()]
    except (OSError, subprocess.CalledProcessError):
        paths = list(root.rglob("*.html"))
    return sorted(p for p in paths if p.is_file()
                  and not (set(p.relative_to(root).parts) & EXCLUDED))


class Anchors(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def asin_of(value: str) -> str | None:
    match = ASIN_RE.search(urlparse(value).path)
    return match.group(1).upper() if match else None


def audit(root: Path, expected: str) -> dict:
    counts: Counter[str] = Counter()
    errors: list[dict[str, str]] = []
    reviews: list[dict[str, str]] = []
    shortlinks: set[str] = set()
    unique_destinations: set[str] = set()
    product_verification_queue: list[dict[str, str]] = []

    def check(source: str, url: str, expected_isbn: str | None = None) -> None:
        p = urlparse(url)
        host = (p.hostname or "").lower()
        scheme = p.scheme.lower()
        allowed_host = host in {"www.amazon.es", "amazon.es", "amzn.to"}
        try:
            port = p.port
        except ValueError:
            port = -1
        if scheme in {"javascript", "data", "vbscript", "file"}:
            errors.append({"source": source, "type": "unsafe_scheme", "url": url})
            return
        if allowed_host and (scheme != "https" or "@" in p.netloc or port is not None):
            errors.append({"source": source, "type": "unsafe_destination", "url": url})
            return
        if not allowed_host and scheme in {"http", "https"} and ("amazon." in host or "amzn." in host):
            foreign = any(host == m or host.endswith("." + m) for m in (
                "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amazon.it"))
            if not foreign or scheme != "https":
                errors.append({"source": source, "type": "unsafe_destination", "url": url})
                return
        if not allowed_host:
            foreign_marketplaces = (
                "amazon.com",
                "amazon.co.uk",
                "amazon.de",
                "amazon.fr",
                "amazon.it",
            )
            if any(host == market or host.endswith("." + market) for market in foreign_marketplaces):
                counts["other_market_link"] += 1
                reviews.append({"source": source, "type": "otro_mercado", "url": url})
            return
        unique_destinations.add(url)
        if host == "amzn.to":
            counts["shortlink_occurrences"] += 1
            shortlinks.add(url)
            return

        params = parse_qs(p.query, keep_blank_values=True)
        if asin_of(url):
            kind = "product"
        elif p.path == "/s":
            kind = "isbn_search"
        elif "tag" in params:
            kind = "other_tagged_amazon"
        else:
            counts["author_or_informational"] += 1
            return
        counts[kind] += 1
        if kind == "isbn_search" and expected_isbn:
            actual_isbns = params.get("k", [])
            if actual_isbns != [str(expected_isbn)]:
                errors.append({
                    "source": source,
                    "type": "isbn_search_mismatch",
                    "url": url,
                    "expected_isbn": str(expected_isbn),
                    "actual_isbn": ",".join(actual_isbns) if actual_isbns else "(sin ISBN)",
                })
        tags = params.get("tag", [])
        if tags != [expected]:
            errors.append({
                "source": source, "type": "missing_or_wrong_tag",
                "url": url, "actual": ",".join(tags) if tags else "(sin tag)"
            })

    pages = html_paths(root)
    counts["html_pages_scanned"] = len(pages)
    for path in pages:
        relative = path.relative_to(root).as_posix()
        parser = Anchors()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        for url in parser.links:
            check(relative, url)

    catalogue_path = root / "data/reading-catalogue.json"
    if catalogue_path.is_file():
        data = json.loads(catalogue_path.read_text(encoding="utf-8"))
        books = [b for b in data.get("libros", []) if b.get("estado") == "publicado"]
        counts["published_books"] = len(books)
        for b in books:
            source = "data/reading-catalogue.json:" + b.get("slug", b.get("id", "?"))
            direct = b.get("url_amazon_afiliada")
            counts["book_product_direct"] += bool(direct)
            counts["book_only_search"] += not bool(direct)
            if not direct:
                product_verification_queue.append({
                    "slug": b.get("slug", ""),
                    "titulo": b.get("titulo", ""),
                    "isbn13": b.get("isbn13", ""),
                    "actual_isbn_search": b.get("amazon_busqueda_isbn", ""),
                    "next_step": "Verify Amazon.es exact edition ASIN, format and language; link direct product or remove affiliate CTA",
                })
            for field in ("amazon_busqueda_isbn", "url_amazon_afiliada"):
                if b.get(field):
                    check(
                        source + "." + field,
                        b[field],
                        expected_isbn=b.get("isbn13") if field == "amazon_busqueda_isbn" else None,
                    )
            for option in b.get("formatos_compra", []):
                url = option.get("url", "")
                if url:
                    counts["format_options"] += 1
                    check(source + ".formatos_compra:" + option.get("formato", "?"), url)
                    verification = option.get("fuente_url", "")
                    if asin_of(url) and asin_of(verification) and asin_of(url) != asin_of(verification):
                        reviews.append({
                            "source": source, "type": "fuente_ASIN_diferente",
                            "formato": option.get("formato", "?"),
                            "product_asin": asin_of(url) or "",
                            "source_asin": asin_of(verification) or "",
                        })
    else:
        errors.append({"source": "data/reading-catalogue.json", "type": "catalogue_missing"})

    return {
        "expected_tag": expected,
        "counts": dict(sorted(counts.items())),
        "unique_destination_count": len(unique_destinations),
        "shortlinks_require_manual_verification": sorted(shortlinks),
        "product_verification_queue": product_verification_queue,
        "errors": errors,
        "manual_review": reviews,
        "scope": "HTML estático tracked + data/reading-catalogue.json; sin JS runtime, red, ventas ni enlaces acortados resueltos",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--tag", help="ID esperado, por defecto de data/reading-import-review.json")
    ap.add_argument("--json", action="store_true", help="Salida JSON")
    args = ap.parse_args()
    root = args.root.resolve()
    if args.tag:
        expected = args.tag
    else:
        config_path = root / "data/reading-import-review.json"
        if not config_path.is_file():
            ap.error("Falta data/reading-import-review.json: indique --tag explícitamente")
        expected = json.loads(config_path.read_text(encoding="utf-8")).get("amazon_tracking_id")
    if not expected or not re.fullmatch(r"[A-Za-z0-9-]+", expected):
        ap.error("Tracking ID esperado inválido")
    report = audit(root, expected)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("Auditoría offline Amazon.es · ID:", expected)
        for key, value in report["counts"].items():
            print(f"  {key}: {value}")
        print("Shortlinks por verificar con Amazon:", report["shortlinks_require_manual_verification"])
        print("Libros pendientes de ASIN exacto:", len(report["product_verification_queue"]))
        print("Errores de tag:", len(report["errors"]))
        print("Comprobaciones manuales adicionales:", len(report["manual_review"]))
        for item in report["errors"][:20]:
            print("ERROR:", item)
        for item in report["manual_review"][:20]:
            print("REVISAR:", item)
        print("Límite:", report["scope"])
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
