"""One autonomous local cycle: current main catalogue -> editorial verification -> Telegram.

Run periodically with a persistent private root. No browser, paid API or Git writes.
"""

from __future__ import annotations

import argparse
import copy
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import sys
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

import requests

from reading_amazon_market import asin_from_url
from reading_editorial_sources import (
    CachedHTTP,
    ProductHTML,
    SourceError,
    penguin_edition,
)
from reading_generic_source import generic_edition, reviewed_hosts
from reading_intake_core import isbn13, normalize_text
from reading_planeta_source import planeta_edition
from reading_telegram import amazon_url, from_reading_catalogue, run

MAIN = "https://raw.githubusercontent.com/davidpd89/web-escritor/main/data/"


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def main_json(name):
    response = requests.get(MAIN + name, timeout=30, allow_redirects=False)
    if response.status_code != 200 or len(response.content) > 8_000_000:
        raise ValueError("Main catalogue/configuration unavailable")
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Main JSON is not an object")
    return data


def editorial_product(document, url, book, source):
    """Accept a unique direct Amazon link on the verified selected edition page."""
    provider = source.get("provider")
    if provider == "penguin" and urlsplit(url).hostname == "www.penguinlibros.com":
        edition = penguin_edition(document, url)
    elif provider == "planeta" and urlsplit(url).hostname == "www.planetadelibros.com":
        edition = planeta_edition(document, url)
    elif provider == "generic":
        edition = generic_edition(source, document, url)
    else:
        raise SourceError("Unsupported editorial provider")
    if (
        isbn13(book.get("isbn13")) != edition["isbn13"]
        or normalize_text(book["titulo"]) != normalize_text(edition["titulo"])
        or {normalize_text(a) for a in book["autores"]}
        != {normalize_text(a) for a in edition["autores"]}
    ):
        raise SourceError("Editorial edition identity changed")
    # Never derive an ASIN from ISBN and never follow an Amazon search link.
    parser = ProductHTML()
    parser.feed(document)
    products = {
        asin for a in parser.links if (asin := asin_from_url(urljoin(url, a["url"])))
    }
    if len(products) != 1:
        raise SourceError("No unique direct Amazon product on editorial edition page")
    published = edition["fecha_publicacion_edicion"]
    date.fromisoformat(published)  # Partial dates fail closed.
    return next(iter(products)), published


def verified_snapshot(catalogue, intake, today, fetch):
    result = copy.deepcopy(catalogue)
    report = {"checked": 0, "resolved": 0, "pending": [], "verified": []}
    sources = [s for s in intake["sources"] if s.get("enabled")]
    tag = intake["amazon_partner_tag"]
    for book in result["libros"]:
        try:
            published = date.fromisoformat(book.get("fecha_publicacion", ""))
        except (TypeError, ValueError):
            continue
        if book.get("estado") != "publicado" or not today - timedelta(
            days=3
        ) <= published <= today + timedelta(days=30):
            continue
        # Until checked today, a due book cannot fall back to stale product/date data.
        url = book.get("fuente_publicacion_url", "")
        source = next(
            (s for s in sources if urlsplit(url).hostname in s.get("hosts", [])), None
        )
        try:
            if not source:
                raise SourceError("Edition source not configured")
            report["checked"] += 1
            document = fetch(url, source)
            asin, actual_date = editorial_product(document, url, book, source)
            book["fecha_publicacion"] = actual_date
            book["url_amazon_afiliada"] = amazon_url(asin, tag)
            report["resolved"] += 1
            report["verified"].append(
                {
                    "id": book["id"],
                    "isbn13": book["isbn13"],
                    "asin": asin,
                    "release_date": actual_date,
                    "source_url": url,
                }
            )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            book["estado"] = "pendiente_verificacion_telegram"
            report["pending"].append(
                {
                    "id": book["id"],
                    "release_date": published.isoformat(),
                    "reason": str(exc)
                    if isinstance(exc, SourceError)
                    else type(exc).__name__,
                }
            )
    return result, report


def cycle(root: Path, live=False):
    root = root.resolve()
    # The scheduler serializes cycles, in addition to SQLite delivery claims.
    catalogue = main_json("reading-catalogue.json")
    intake = main_json("reading-intake-config.json")
    today = datetime.now(ZoneInfo("Europe/Madrid")).date()
    clients = {}

    def fetch(url, source):
        sid = source["id"]
        if sid not in clients:
            provider = source.get("provider")
            if provider == "penguin":
                hosts = ("www.penguinlibros.com",)
            elif provider == "planeta":
                hosts = ("www.planetadelibros.com",)
            else:
                hosts, _ = reviewed_hosts(source)
            clients[sid] = CachedHTTP(
                root / "editorial-cache" / sid, hosts, budget=50, delay=1.5
            )
        return clients[sid].get(url, ttl=3600).decode("utf-8")

    snapshot, verification = verified_snapshot(catalogue, intake, today, fetch)
    atomic_json(root / "catalogue.json", snapshot)
    atomic_json(
        root / "editorial-verification.json",
        {"date": today.isoformat(), **verification},
    )
    catalog = from_reading_catalogue(root / "catalogue.json", root / "channels.json")
    if live:
        # This private token file never enters command arguments, reports or Git.
        os.environ["READING_TELEGRAM_BOT_TOKEN"] = (
            (root / "bot-token.txt").read_text(encoding="utf-8").strip()
        )
    deliveries = run(catalog, today, root / "deliveries.db", live)
    attention = any(
        r["status"]
        in {
            "uncertain",
            "rejected",
            "skipped:sending",
            "skipped:uncertain",
            "skipped:rejected",
        }
        or r["status"].startswith(("retry:", "skipped:retry:"))
        for r in deliveries
    )
    report = {
        "at": datetime.now(ZoneInfo("Europe/Madrid")).isoformat(),
        "live": live,
        "status": "needs_attention"
        if attention
        or any(p["release_date"] == today.isoformat() for p in verification["pending"])
        else "ok",
        "eligible": len(catalog["books"]),
        "verification": verification,
        "deliveries": deliveries,
    }
    atomic_json(root / "last-run.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    try:
        report = cycle(args.root, args.send)
        if report["status"] == "needs_attention":
            return 2
        return 0
    except Exception as exc:
        # Do not serialize requests exceptions or secrets, including in failure paths.
        atomic_json(
            args.root / "last-run.json",
            {
                "status": "failed",
                "error_type": type(exc).__name__,
                "at": datetime.now(ZoneInfo("Europe/Madrid")).isoformat(),
            },
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
