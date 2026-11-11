"""Autonomous cycle: current main catalogue -> editorial verification -> Telegram.

Run locally with SQLite, or on GitHub Actions with durable remote checkpoints.
No browser or paid provider API. Private runtime files never become public assets.
"""

from __future__ import annotations

import argparse
import copy
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import re
import sys
import traceback
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
from reading_ttl_source import HOST as TTL_HOST, ttl_edition
from reading_telegram import (
    SEND_AT,
    amazon_url,
    digest_key,
    from_reading_catalogue,
    run,
    smoke,
    weekly_key,
)

MAIN = "https://raw.githubusercontent.com/davidpd89/web-escritor/main/data/"

# Sanity ceiling for the project's own data files, not a catalogue-size limit: it guards
# against a corrupt or runaway response, never against the catalogue growing. The catalogue
# grows every night with the ingesta, so a cap near its real size is a time bomb (it broke
# the scheduled publisher the day it crossed 8 MB). Keep it well above the real file; the
# regression test in tests/ fails first in the local gate when the catalogue nears it.
MAX_MAIN_JSON_BYTES = 64_000_000


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
    if response.status_code != 200 or len(response.content) > MAX_MAIN_JSON_BYTES:
        raise ValueError("Main catalogue/configuration unavailable")
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Main JSON is not an object")
    return data


def editorial_product(document, url, book, source, today=None):
    """Accept a unique direct Amazon link on the verified selected edition page."""
    provider = source.get("provider")
    if provider == "penguin" and urlsplit(url).hostname == "www.penguinlibros.com":
        edition = penguin_edition(document, url)
    elif provider == "planeta" and urlsplit(url).hostname == "www.planetadelibros.com":
        edition = planeta_edition(document, url)
    elif provider == "todostuslibros" and urlsplit(url).hostname == TTL_HOST:
        # Books seeded by release date: CEGAL record, no Amazon link on the page.
        edition = ttl_edition(document, url)
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
    published = edition["fecha_publicacion_edicion"]
    date.fromisoformat(published)  # Partial dates fail closed.
    if len(products) == 1:
        return next(iter(products)), published
    if not products and today is not None:
        # Many publishers never link Amazon: the edition and date are verified here,
        # the product comes from the nightly Amazon check of this same book.
        asin = catalogue_print_asin(book, today)
        if asin:
            return asin, published
    raise SourceError("No unique direct Amazon product on editorial edition page")


AMAZON_FRESH_DAYS = 2


def catalogue_print_asin(book, today):
    """The single print product the catalogue re-read on Amazon recently, if any."""
    since = (today - timedelta(days=AMAZON_FRESH_DAYS)).isoformat()
    found = {
        asin
        for offer in book.get("formatos_compra") or []
        if offer.get("formato") in {"tapa-blanda", "tapa-dura"}
        and str(offer.get("fecha_verificacion") or "") >= since
        and (asin := asin_from_url(offer.get("fuente_url") or offer.get("url") or ""))
    }
    return next(iter(found)) if len(found) == 1 else None


def amazon_product(book, url, today):
    """Books found by the Amazon intake: their source IS the product page, re-read every night."""
    asin = asin_from_url(url)
    if not asin:
        raise SourceError("No direct Amazon product in source")
    checked = max(
        str(book.get("precios_amazon_revision") or ""),
        str(book.get("fecha_verificacion") or ""),
    )
    if checked < (today - timedelta(days=AMAZON_FRESH_DAYS)).isoformat():
        raise SourceError("Amazon product data not refreshed recently")
    published = book["fecha_publicacion"]
    date.fromisoformat(published)
    return asin, published


# Failures that a later cycle can fix (network, request budget, robots.txt unreachable, cut response).
# Everything else is a verdict on the edition itself (no single Amazon product, changed identity,
# missing cover...): the book is excluded from today's posts on purpose, which is not an incident.
TRANSIENT_SOURCE_ERRORS = (
    "Presupuesto diario de solicitudes agotado",
    "No se ha podido verificar robots.txt",
    "Respuesta editorial incompleta",
)


def is_transient(exc) -> bool:
    if isinstance(exc, SourceError):
        return str(exc) in TRANSIENT_SOURCE_ERRORS
    return isinstance(exc, OSError)


def verified_snapshot(catalogue, intake, today, fetch):
    result = copy.deepcopy(catalogue)
    report = {"checked": 0, "resolved": 0, "pending": [], "verified": []}
    sources = [s for s in intake["sources"] if s.get("enabled")]
    tag = intake["amazon_partner_tag"]
    window = []
    for book in result["libros"]:
        try:
            published = date.fromisoformat(book.get("fecha_publicacion", ""))
        except (TypeError, ValueError):
            continue
        if book.get("estado") == "publicado" and today - timedelta(
            days=3
        ) <= published <= today + timedelta(days=30):
            window.append((book, published))
    # The per-source request budget is finite: spend it on today's books first,
    # then upcoming dates in order, and only then the recent past (already announced).
    window.sort(key=lambda item: (item[1] < today, abs((item[1] - today).days)))
    for book, published in window:
        # Until checked today, a due book cannot fall back to stale product/date data.
        url = book.get("fuente_publicacion_url", "")
        source = next(
            (s for s in sources if urlsplit(url).hostname in s.get("hosts", [])), None
        )
        try:
            if urlsplit(url).hostname in {"amazon.es", "www.amazon.es"}:
                report["checked"] += 1
                asin, actual_date = amazon_product(book, url, today)
            else:
                if not source:
                    raise SourceError("Edition source not configured")
                report["checked"] += 1
                document = fetch(url, source)
                asin, actual_date = editorial_product(
                    document, url, book, source, today
                )
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
                    "transient": is_transient(exc),
                }
            )
    return result, report


MIN_COVER_BYTES = 5000  # Amazon answers a missing cover with a ~1 KB placeholder GIF


def real_cover_url(url, get=requests.get):
    """True when the URL serves a real image (not a placeholder, not an error page)."""
    try:
        response = get(url, timeout=10, allow_redirects=True)
    except requests.RequestException:
        return False
    kind = response.headers.get("Content-Type", "")
    return (
        response.status_code == 200
        and kind.startswith("image/")
        and "gif" not in kind
        and len(response.content) >= MIN_COVER_BYTES
    )


def cover_resolver(fixes, get=requests.get, fetch_json=None):
    """For books that still carry our typographic cover, look for the real one before posting.

    Order: Amazon image of that ASIN, then Open Library and Google Books by ISBN. When one exists the
    post uses it and the fix is reported as «fallo nuestro» (the nightly cover pass missed it); when
    none exists the typographic cover is the right one and is kept."""
    from reading_amazon_market import fallback_cover_urls

    if fetch_json is None:
        def fetch_json(url):
            return get(url, timeout=10).json()

    memo = {}

    def resolve(book):
        if not book.get("generated_cover"):
            return None
        key = book.get("id") or book["asin"]
        if key in memo:
            return memo[key]
        candidates = []
        if re.fullmatch(r"[0-9]{9}[0-9X]", book.get("asin", "")):
            candidates.append(
                ("Amazon", f"https://images-na.ssl-images-amazon.com/images/P/{book['asin']}.01.LZZZZZZZ.jpg")
            )
        candidates += fallback_cover_urls({"isbn13": book.get("isbn13")}, fetch_json)
        found = next(((name, url) for name, url in candidates if real_cover_url(url, get)), None)
        memo[key] = found[1] if found else None
        fixes.append(
            {
                "id": book.get("id"),
                "title": book.get("title"),
                "source": found[0] if found else None,
                "verdict": "fallo nuestro: había portada real" if found else "sin portada real: tipográfica",
            }
        )
        return memo[key]

    return resolve


def cycle(root: Path, live=False, github_state=False, test_asin=None):
    root = root.resolve()
    now = datetime.now(ZoneInfo("Europe/Madrid"))
    if not test_asin and now.time() < SEND_AT:
        # The day goes out at 11:30 Madrid; earlier cycles do no work at all.
        report = {"at": now.isoformat(), "live": live, "status": "waiting", "deliveries": []}
        atomic_json(root / "last-run.json", report)
        return report
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
            elif provider == "todostuslibros":
                hosts = (TTL_HOST,)
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
    groups = {
        g["id"]: g
        for g in main_json("communities.json").get("groups", [])
        if isinstance(g, dict) and g.get("id")
    }
    catalog = from_reading_catalogue(
        root / "catalogue.json", root / "channels.json", groups
    )
    catalog["digests"] = [
        digest_key(today.isoformat()),
        weekly_key(today.isoformat()),
    ]
    cover_fixes = []
    store = None
    if live:
        # This private token file never enters command arguments, reports or Git.
        os.environ["READING_TELEGRAM_BOT_TOKEN"] = (
            (root / "bot-token.txt").read_text(encoding="utf-8").strip()
        )
        if github_state:
            from reading_telegram_state import remote_state

            store = remote_state("smoke" if test_asin else "daily")
    db_path = root / ("smoke.db" if test_asin else "deliveries.db")
    if store:
        store.restore(db_path, catalog)
    checkpoint = store.checkpoint if store else None
    if test_asin:
        deliveries = smoke(catalog, test_asin, db_path, live, checkpoint=checkpoint)
    else:
        deliveries = run(
            catalog,
            today,
            db_path,
            live,
            checkpoint=checkpoint,
            now=now,
            cover_resolver=cover_resolver(cover_fixes) if live else None,
        )
    # Ambiguous or rejected deliveries alert in the cycle where they happen; afterwards they are
    # 'skipped:*' (already reported, never resent) and must not keep every cycle of the day red.
    attention = any(
        r["status"] in {"uncertain", "rejected", "skipped:sending"}
        or r["status"].startswith(("uncertain:", "retry:", "skipped:retry:"))
        for r in deliveries
    )
    report = {
        "at": datetime.now(ZoneInfo("Europe/Madrid")).isoformat(),
        "live": live,
        "status": "needs_attention"
        if attention
        or any(
            p["release_date"] == today.isoformat() and p.get("transient", True)
            for p in verification["pending"]
        )
        else "ok",
        "eligible": len(catalog["books"]),
        "verification": verification,
        "deliveries": deliveries,
        "cover_fixes": cover_fixes,
    }
    atomic_json(root / "last-run.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--github-state", action="store_true")
    parser.add_argument("--test-asin")
    args = parser.parse_args()
    try:
        report = cycle(args.root, args.send, args.github_state, args.test_asin)
        if report["status"] == "needs_attention":
            return 2
        return 0
    except Exception as exc:
        # Do not serialize requests exceptions or secrets, including in failure paths: only the type and
        # where it happened (file:line function), never the message. 09/11 the run died after 6 min with
        # no trace at all.
        where = [
            f"{Path(f.filename).name}:{f.lineno} {f.name}"
            for f in traceback.extract_tb(exc.__traceback__)
        ][-6:]
        print(f"Telegram cycle failed: {type(exc).__name__} at " + " <- ".join(reversed(where)), file=sys.stderr)
        atomic_json(
            args.root / "last-run.json",
            {
                "status": "failed",
                "error_type": type(exc).__name__,
                "where": where,
                "at": datetime.now(ZoneInfo("Europe/Madrid")).isoformat(),
            },
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
