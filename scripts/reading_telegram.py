"""Isolated book-channel pilot, based on Bet's HTTP/HTML Telegram transport."""

from __future__ import annotations

import argparse
from contextlib import closing
from datetime import date, datetime
from html import escape
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
from urllib.parse import urlencode, parse_qs, urlsplit
from zoneinfo import ZoneInfo

import requests
from reading_amazon_market import asin_from_url


def amazon_url(asin: str, tag: str = "") -> str:
    if not re.fullmatch(r"[A-Z0-9]{10}", asin):
        raise ValueError("ASIN must contain exactly 10 uppercase letters/digits")
    return f"https://www.amazon.es/dp/{asin}" + (
        "?" + urlencode({"tag": tag}) if tag else ""
    )


def from_reading_catalogue(path: Path, channels_path: Path) -> dict:
    """Adapt the existing catalogue, preserving reviewed Amazon destinations."""
    source = json.loads(path.read_text(encoding="utf-8"))
    config = json.loads(channels_path.read_text(encoding="utf-8"))
    if config.get("enabled") is not True:
        raise ValueError("Telegram configuration is disabled")
    channels = config["channels"]
    if not channels or len({c["chat_id"] for c in channels}) != len(channels):
        raise ValueError("Unique channel destinations required")
    for channel in channels:
        if not channel["chat_id"] or not channel["token_env"]:
            raise ValueError("Missing channel configuration")
    categories = {}
    for relation in source["libro_categorias"]:
        categories.setdefault(relation["libro_id"], []).append(relation["categoria_id"])
    books, pending, seen = [], [], set()
    for book in source["libros"]:
        published = book.get("fecha_publicacion", "")
        url = book.get("url_amazon_afiliada", "")
        asin = asin_from_url(url)
        try:
            exact = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", published))
            if exact:
                date.fromisoformat(published)
        except (ValueError, TypeError):
            exact = False
        if (
            book.get("estado") != "publicado"
            or not exact
            or not asin
            or not book.get("fuente_publicacion_url")
            or not book.get("titulo")
            or not book.get("autores")
        ):
            pending.append(book.get("id"))
            continue
        if asin in seen:
            raise ValueError("Duplicate product edition in source catalogue")
        seen.add(asin)
        books.append(
            {
                "asin": asin,
                "title": book["titulo"],
                "author": ", ".join(book["autores"]),
                "release_date": published,
                "categories": categories.get(book["id"], []),
                "source_url": book["fuente_publicacion_url"],
                "amazon_url": url,
            }
        )
    return {
        "demo": config.get("demo", False),
        "channels": channels,
        "books": books,
        "pending": pending,
    }


def message(book: dict, tag: str) -> str:
    url = book.get("amazon_url") or amazon_url(book["asin"], tag)
    text = (
        f"📚 <b>Novedad de hoy</b>\n\n<b>{escape(book['title'])}</b>\n"
        f"{escape(book['author'])}\n📅 {book['release_date']}\n\n"
        f'<a href="{escape(url, quote=True)}">Ver en Amazon</a>'
    )
    if tag or parse_qs(urlsplit(url).query).get("tag"):
        text += "\n\nEnlace de afiliado. Podemos recibir una comisión por tu compra."
    return text


def send(token: str, chat_id: str, text: str) -> tuple[str, int | None]:
    """Never expose requests exceptions: they can contain the bot token in the URL."""
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
        data = response.json()
        if response.status_code == 200 and data.get("ok") is True:
            mid = data.get("result", {}).get("message_id")
            if type(mid) is int:
                return "sent", mid
        # A definitive client rejection can be retried on a later cycle.
        if 400 <= response.status_code < 500 and data.get("ok") is False:
            return "rejected", None
    except (requests.RequestException, ValueError, AttributeError, TypeError):
        pass
    return "uncertain", None


def run(
    catalog: dict,
    today: date,
    db_path: Path,
    live: bool = False,
    tag: str = "",
    sender=send,
) -> list[dict]:
    due = [b for b in catalog["books"] if b["release_date"] == today.isoformat()]
    jobs = [
        (c, b)
        for c in catalog["channels"]
        for b in due
        if not c.get("categories")
        or set(b.get("categories", [])) & set(c["categories"])
    ]
    if not live:
        return [
            {"chat_id": c["chat_id"], "status": "preview", "text": message(b, tag)}
            for c, b in jobs
        ]
    if catalog.get("demo", False):
        raise ValueError("Demo catalogs cannot send real messages")
    tokens = {
        c["token_env"]: os.environ.get(c["token_env"], "") for c in catalog["channels"]
    }
    if not all(tokens.values()):
        raise ValueError("Configure all bot token environment variables before sending")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with closing(sqlite3.connect(db_path, timeout=30)) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS deliveries (chat TEXT, asin TEXT, status TEXT, message_id INTEGER, PRIMARY KEY(chat, asin))"
        )
        for channel, book in jobs:
            key = (channel["chat_id"], book["asin"])
            # Commit the claim before HTTP. A crash leaves a visible 'sending' row,
            # which deliberately blocks automatic resends after an ambiguous delivery.
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT status FROM deliveries WHERE chat=? AND asin=?", key
            ).fetchone()
            if row:
                db.commit()
                results.append(
                    {"chat_id": key[0], "asin": key[1], "status": "skipped:" + row[0]}
                )
                continue
            db.execute("INSERT INTO deliveries VALUES (?, ?, 'sending', NULL)", key)
            db.commit()
            status, mid = sender(
                tokens[channel["token_env"]], key[0], message(book, tag)
            )
            db.execute(
                "UPDATE deliveries SET status=?, message_id=? WHERE chat=? AND asin=?",
                (status, mid, *key),
            )
            db.commit()
            results.append({"chat_id": key[0], "asin": key[1], "status": status})
            time.sleep(1)  # Conservative pacing for this small pilot.
    return results


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog", type=Path, default=Path("data/reading-catalogue.json")
    )
    parser.add_argument("--channels", type=Path, required=True)
    parser.add_argument(
        "--db", type=Path, default=Path(".local/telegram/deliveries.db")
    )
    parser.add_argument("--date", type=date.fromisoformat, help="Preview date only")
    parser.add_argument(
        "--send", action="store_true", help="Enable real Telegram delivery"
    )
    parser.add_argument(
        "--watch", action="store_true", help="Recheck catalog every five minutes"
    )
    args = parser.parse_args()
    if args.send and args.date:
        parser.error("--date is only allowed for preview")
    try:
        while True:
            today = args.date or datetime.now(ZoneInfo("Europe/Madrid")).date()
            catalog = from_reading_catalogue(args.catalog, args.channels)
            print(
                json.dumps(
                    {
                        "eligible": len(catalog["books"]),
                        "pending": len(catalog["pending"]),
                    }
                ),
                flush=True,
            )
            results = run(catalog, today, args.db, args.send)
            print(json.dumps(results, ensure_ascii=False), flush=True)
            if not args.watch:
                if any(
                    r["status"].startswith(
                        (
                            "uncertain",
                            "rejected",
                            "skipped:uncertain",
                            "skipped:sending",
                            "skipped:rejected",
                        )
                    )
                    for r in results
                ):
                    raise SystemExit(1)
                break
            time.sleep(300)
    except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
        parser.exit(
            1,
            f"Pilot stopped ({type(exc).__name__}); check catalog, configuration and database.\n",
        )


if __name__ == "__main__":
    main()
