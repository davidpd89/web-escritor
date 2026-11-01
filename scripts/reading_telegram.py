"""Daily release channel with verified covers and persistent delivery state."""

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
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import requests
from reading_amazon_market import asin_from_url


def cover_url(book: dict) -> str | None:
    path = book.get("portada_local", "")
    if (
        book.get("portada_edicion_verificada") is True
        and isinstance(path, str)
        and re.fullmatch(
            r"/assets/reading-covers/[a-zA-Z0-9_-]+\.(?:webp|jpg|jpeg|png)", path
        )
    ):
        return "https://davidportodiaz.com" + path
    return None


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
    genre_names = {
        c["id"]: c["nombre"]
        for c in source.get("categorias", [])
        if c.get("tipo") == "genero" and c.get("activa", True)
    }
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
                "genres": list(
                    dict.fromkeys(
                        genre_names[c]
                        for c in categories.get(book["id"], [])
                        if c in genre_names
                    )
                ),
                "source_url": book["fuente_publicacion_url"],
                "amazon_url": url,
                "cover_url": cover_url(book),
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
    genres = book.get("genres", [])
    genre_line = f"🏷️ {escape(', '.join(genres[:3]))}\n" if genres else ""
    text = (
        f"📚 <b>Novedad de hoy</b>\n\n<b>{escape(book['title'])}</b>\n"
        f"{escape(book['author'])}\n📅 {book['release_date']}\n{genre_line}\n"
        f'<a href="{escape(url, quote=True)}">Ver en Amazon</a>'
    )
    return text


def send(
    token: str, chat_id: str, text: str, photo_url: str | None = None
) -> tuple[str, int | None]:
    """Never expose requests exceptions: they can contain the bot token in the URL."""
    try:
        method = "sendPhoto" if photo_url else "sendMessage"
        payload = {"chat_id": chat_id, "parse_mode": "HTML"}
        if photo_url:
            payload.update(photo=photo_url, caption=text)
        else:
            payload.update(text=text, link_preview_options={"is_disabled": True})
        response = requests.post(
            f"https://api.telegram.org/bot{token}/{method}",
            json=payload,
            timeout=15,
        )
        data = response.json()
        if response.status_code == 200 and data.get("ok") is True:
            mid = data.get("result", {}).get("message_id")
            if type(mid) is int:
                return "sent", mid
        # A rejected photo has not been delivered; text fallback is safe.
        if photo_url and response.status_code == 400 and data.get("ok") is False:
            return send(token, chat_id, text)
        if response.status_code == 429 and data.get("ok") is False:
            try:
                delay = max(1, int(data.get("parameters", {}).get("retry_after", 900)))
            except (ValueError, TypeError, AttributeError):
                delay = 900
            return f"retry:{int(time.time()) + delay}", None
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
    checkpoint=None,
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
                if row[0].startswith("retry:") and time.time() >= int(
                    row[0].split(":", 1)[1]
                ):
                    db.execute("DELETE FROM deliveries WHERE chat=? AND asin=?", key)
                    row = None
            if row:
                db.commit()
                results.append(
                    {"chat_id": key[0], "asin": key[1], "status": "skipped:" + row[0]}
                )
                continue
            db.execute("INSERT INTO deliveries VALUES (?, ?, 'sending', NULL)", key)
            db.commit()
            if checkpoint:
                checkpoint(
                    db_path
                )  # Must be durable remotely BEFORE the HTTP side effect.
            status, mid = sender(
                tokens[channel["token_env"]],
                key[0],
                message(book, tag),
                book.get("cover_url"),
            )
            db.execute(
                "UPDATE deliveries SET status=?, message_id=? WHERE chat=? AND asin=?",
                (status, mid, *key),
            )
            db.commit()
            if checkpoint:
                checkpoint(db_path)
            results.append({"chat_id": key[0], "asin": key[1], "status": status})
            time.sleep(1)  # Conservative pacing for this small pilot.
    return results


def smoke(
    catalog: dict,
    asin: str,
    db_path: Path,
    live: bool = False,
    sender=send,
    checkpoint=None,
) -> list[dict]:
    """Exercise one reviewed edition without claiming it was released today.

    Use a separate delivery database so the test cannot suppress a daily job.
    """
    selected = [book for book in catalog["books"] if book["asin"] == asin]
    if len(selected) != 1:
        raise ValueError("Choose one eligible ASIN from the existing catalogue")
    test_catalog = {**catalog, "books": selected}

    def test_text(text):
        return text.replace(
            "📚 <b>Novedad de hoy</b>",
            "🧪 <b>PRUEBA · ficha de libro</b>\nNo es una novedad de hoy.",
            1,
        )

    def test_sender(token, chat_id, text, photo_url=None):
        return sender(token, chat_id, test_text(text), photo_url)

    results = run(
        test_catalog,
        date.fromisoformat(selected[0]["release_date"]),
        db_path,
        live,
        sender=test_sender,
        checkpoint=checkpoint,
    )
    for result in results:
        if "text" in result:
            result["text"] = test_text(result["text"])
    return results


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog", type=Path, default=Path("data/reading-catalogue.json")
    )
    parser.add_argument("--channels", type=Path, required=True)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--date", type=date.fromisoformat, help="Preview date only")
    parser.add_argument(
        "--test-asin", help="One labelled test edition; uses a separate smoke database"
    )
    parser.add_argument(
        "--send", action="store_true", help="Enable real Telegram delivery"
    )
    parser.add_argument(
        "--watch", action="store_true", help="Recheck catalog every five minutes"
    )
    args = parser.parse_args()
    if args.send and args.date:
        parser.error("--date is only allowed for preview")
    if args.test_asin and (args.watch or args.date):
        parser.error("--test-asin cannot be combined with --watch or --date")
    db_path = args.db or Path(
        ".local/telegram/smoke.db"
        if args.test_asin
        else ".local/telegram/deliveries.db"
    )
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
            if args.test_asin:
                if db_path.resolve() == Path(".local/telegram/deliveries.db").resolve():
                    raise ValueError("Smoke test requires its own database")
                results = smoke(catalog, args.test_asin, db_path, args.send)
            else:
                results = run(catalog, today, db_path, args.send)
            print(json.dumps(results, ensure_ascii=False), flush=True)
            if not args.watch:
                if any(
                    r["status"].startswith(
                        (
                            "uncertain",
                            "rejected",
                            "retry",
                            "skipped:uncertain",
                            "skipped:sending",
                            "skipped:rejected",
                            "skipped:retry",
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
