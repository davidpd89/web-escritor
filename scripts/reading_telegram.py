"""Daily release channel with verified covers and persistent delivery state."""

from __future__ import annotations

import argparse
from contextlib import closing
from datetime import date, datetime, time as dtime, timedelta
from html import escape, unescape
import math
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
from urllib.parse import parse_qs, urlencode, urlsplit
from zoneinfo import ZoneInfo

import requests
from reading_amazon_market import asin_from_url, generated_cover


def cover_url(book: dict) -> str | None:
    """Portada publicada en la web. La tipográfica propia vale siempre (la hacemos nosotros con el título
    y el autor de esa edición); una cubierta de fuera solo si se verificó que es de esa edición."""
    path = book.get("portada_local", "")
    if (
        (book.get("portada_edicion_verificada") is True or generated_cover(book))
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


CHANNEL_MODES = {"books", "digest"}
CHANNEL_PERIODS = {"daily", "weekly"}


def edition_note(book: dict) -> str:
    """Descripción de respaldo cuando aún no hay sinopsis: la ficha de la edición de la web (formato,
    páginas, cómo la clasifica la editorial) sin repetir título, autor ni fecha, que ya van en el mensaje."""
    text = str(book.get("descripcion_breve") or "").strip()
    lead = f"{book.get('titulo', '')}, de {', '.join(book.get('autores') or [])}. "
    if text.startswith(lead):
        text = text[len(lead):]
    text = re.sub(r"\s*Publicación editorial: [\d-]+\.?$", "", text)
    return text[:1].upper() + text[1:]


def resolve_groups(channels: list[dict], groups: dict | None) -> list[dict]:
    """Un canal privado puede nombrar un grupo público de data/communities.json («group»): de ahí salen
    sus categorías y su nombre, así el reparto por género se revisa en el repositorio y el JSON privado
    solo guarda destinos."""
    resolved = []
    for channel in channels:
        channel = dict(channel)
        if channel.get("group"):
            group = (groups or {}).get(channel["group"])
            if group is None:
                raise ValueError("Channel names an unknown community group")
            channel.setdefault("categories", list(group.get("categories", [])))
            if group.get("categories"):
                channel.setdefault("label", group.get("name", ""))
        resolved.append(channel)
    return resolved


def from_reading_catalogue(path: Path, channels_path: Path, groups: dict | None = None) -> dict:
    """Adapt the existing catalogue, preserving reviewed Amazon destinations."""
    source = json.loads(path.read_text(encoding="utf-8"))
    config = json.loads(channels_path.read_text(encoding="utf-8"))
    if config.get("enabled") is not True:
        raise ValueError("Telegram configuration is disabled")
    channels = resolve_groups(config["channels"], groups)
    if not channels or len({c["chat_id"] for c in channels}) != len(channels):
        raise ValueError("Unique channel destinations required")
    for channel in channels:
        if channel.get("platform") == "discord":
            # The webhook URL is the credential: it lives only inside the private channels JSON.
            if not channel["chat_id"] or not DISCORD_WEBHOOK.fullmatch(
                channel.get("webhook", "")
            ):
                raise ValueError("Missing channel configuration")
        elif not channel["chat_id"] or not channel["token_env"]:
            raise ValueError("Missing channel configuration")
        if channel.get("mode", "books") not in CHANNEL_MODES or channel.get(
            "period", "daily"
        ) not in CHANNEL_PERIODS:
            raise ValueError("Unknown channel mode or period")
        if channel.get("period") == "weekly" and channel.get("mode") != "digest":
            raise ValueError("Weekly channels send one digest")
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
                "isbn13": str(book.get("isbn13") or ""),
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
                "generated_cover": bool(generated_cover(book)),
                "publisher": str(book.get("editorial") or ""),
                "synopsis": str(book.get("sinopsis_breve") or "")
                or edition_note(book),
                "web_url": f"https://davidportodiaz.com/recomendaciones/libros/{book['slug']}/"
                if re.fullmatch(r"[a-z0-9-]+", str(book.get("slug") or ""))
                else "",
            }
        )
    return {
        "demo": config.get("demo", False),
        "channels": channels,
        "books": books,
        "pending": pending,
    }


# Amazon.es acepta varios ISBN en el filtro p_66 separados por «|» (probado con 60: devuelve sus ediciones).
# Con más libros el resumen lleva varios enlaces, uno por cada bloque de 60.
DIGEST_MAX_ISBNS = 60
DIGEST_MAX_TITLES = 12
SEND_AT = dtime(11, 30)  # Hora de Madrid a la que salen todos los envíos del día.
WEEK_DAYS = 7
MONTHS = (
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre"
).split()


def human_date(day: str, year: bool = False) -> str:
    d = date.fromisoformat(day)
    return f"{d.day} de {MONTHS[d.month - 1]}" + (f" de {d.year}" if year else "")


def isbn_search_url(isbns: list[str], tag: str = "") -> str:
    query = {"i": "stripbooks", "rh": "p_66:" + "|".join(isbns[:DIGEST_MAX_ISBNS])}
    if tag:
        query["tag"] = tag
    return "https://www.amazon.es/s?" + urlencode(query, safe="|:")


def digest_key(day: str) -> str:
    return f"digest-{day}"


def weekly_key(monday: str) -> str:
    return f"weekly-{monday}"


def tag_from_books(books: list[dict]) -> str:
    return next(
        (
            found[0]
            for b in books
            if (found := parse_qs(urlsplit(b.get("amazon_url", "")).query).get("tag"))
        ),
        "",
    )


def digest(
    books: list[dict],
    day: str,
    tag: str = "",
    label: str = "",
    until: str = "",
) -> dict | None:
    """Un único mensaje: los títulos y uno o varios enlaces de Amazon filtrados por sus ISBN.

    Diario («Aquí tienes las publicaciones del día…») o semanal si se da `until`
    («Próximos lanzamientos del … al …», con la fecha de cada libro)."""
    isbns = list(dict.fromkeys(b["isbn13"] for b in books if b.get("isbn13")))
    if not isbns:
        return None
    tag = tag or tag_from_books(books)
    books = sorted(books, key=lambda b: (b["release_date"], b["title"])) if until else books
    lines = [
        (f"• {human_date(b['release_date'])}: " if until else "• ")
        + f"<b>{escape(b['title'])}</b> — {escape(b['author'])}"
        for b in books[:DIGEST_MAX_TITLES]
    ]
    if len(books) > DIGEST_MAX_TITLES:
        lines.append(f"…y {len(books) - DIGEST_MAX_TITLES} más")
    chunks = [isbns[i : i + DIGEST_MAX_ISBNS] for i in range(0, len(isbns), DIGEST_MAX_ISBNS)]
    links = []
    for n, chunk in enumerate(chunks):
        if len(chunks) == 1:
            text = f"Ver los {len(chunk)} en Amazon" if len(chunk) > 1 else "Ver en Amazon"
        else:
            first = n * DIGEST_MAX_ISBNS + 1
            text = f"Ver en Amazon ({first}–{first + len(chunk) - 1})"
        links.append(f'👉 <a href="{escape(isbn_search_url(chunk, tag), quote=True)}">{text}</a>')
    count = f"{len(books)} libro" + ("s" if len(books) != 1 else "")
    if until:
        head = f"🗓️ <b>Próximos lanzamientos del {human_date(day)} al {human_date(until)}</b>"
        key = weekly_key(day)
    else:
        head = f"📚 <b>Aquí tienes las publicaciones del día {human_date(day)}</b>"
        key = digest_key(day)
    sub = f"{escape(label)} · {count}" if label else count
    text = (
        f"{head}\n{sub}\n\n" + "\n".join(lines) + "\n\n" + "\n".join(links) + "\n#publicidad"
    )
    return {"asin": key, "digest": True, "text": text, "release_date": day}


CAPTION_LIMIT = 1024


def visible_length(html_text: str) -> int:
    return len(unescape(re.sub(r"<[^>]+>", "", html_text)))


def shorten(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[: max(0, limit - 1)].rsplit(" ", 1)[0].rstrip(",;:.")
    return cut + "…" if cut else ""


def message(book: dict, tag: str) -> str:
    """Ficha de un libro. Cabe en el pie de una foto de Telegram (1024 caracteres visibles):
    si no, la sinopsis se acorta."""
    if book.get("digest"):
        return book["text"]
    url = book.get("amazon_url") or amazon_url(book["asin"], tag)
    genres = book.get("genres", [])
    meta = [f"📅 {human_date(book['release_date'], year=True)}"]
    if book.get("publisher"):
        meta.insert(0, f"🏢 {escape(book['publisher'])}")
    head = (
        f"📚 <b>Novedad de hoy</b>\n\n<b>{escape(book['title'])}</b>\n"
        f"✍️ {escape(book['author'])}\n" + " · ".join(meta) + "\n"
        + (f"🏷️ {escape(', '.join(genres[:3]))}\n" if genres else "")
    )
    tail = f'\n<a href="{escape(url, quote=True)}">Ver en Amazon</a> · #publicidad'
    if book.get("web_url"):
        tail += f' · <a href="{escape(book["web_url"], quote=True)}">Ficha</a>'
    room = CAPTION_LIMIT - 24 - visible_length(head + tail)
    blurb = shorten(book.get("synopsis", ""), min(320, room)) if room > 40 else ""
    return head + (f"\n<i>{escape(blurb)}</i>\n" if blurb else "") + tail


DISCORD_WEBHOOK = re.compile(
    r"https://(?:discord|discordapp)\.com/api/webhooks/\d+/[A-Za-z0-9_-]+"
)
DISCORD_MAX_CHARS = 2000


def to_discord(text: str) -> str:
    """Telegram HTML to Discord markdown (may exceed 2000 chars: see discord_parts)."""
    text = re.sub(
        r'<a href="([^"]+)">(.*?)</a>',
        lambda m: f"[{m.group(2)}](<{unescape(m.group(1))}>)",
        text,
    )
    text = re.sub(r"</?i>", "*", re.sub(r"</?b>", "**", text))
    return unescape(text)


def discord_parts(text: str) -> list[str]:
    """Discord admits 2000 characters per message. A long digest (several Amazon links of 60 ISBN)
    goes out as consecutive messages cut at line boundaries; a single overlong line is cut hard."""
    parts, current = [], ""
    for line in to_discord(text).split("\n"):
        while len(line) > DISCORD_MAX_CHARS:
            if current:
                parts.append(current)
                current = ""
            parts.append(line[:DISCORD_MAX_CHARS])
            line = line[DISCORD_MAX_CHARS:]
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > DISCORD_MAX_CHARS:
            parts.append(current)
            current = line
        else:
            current = candidate
    if current.strip():
        parts.append(current)
    return [p for p in parts if p.strip()] or [""]


def failure_reason(platform: str, method: str, code, description) -> None:
    """Print why a delivery was not confirmed, so a red run says what happened.

    Only the HTTP code and the API description ("Forbidden: bot is not a member of the channel chat"),
    never the request URL (it carries the bot token), the webhook or the chat.
    """
    text = re.sub(r"\s+", " ", str(description or ""))[:160]
    print(f"{platform} {method}: HTTP {code} {text}".rstrip(), file=sys.stderr)


def send_discord(
    webhook: str, chat_id: str, text: str, photo_url: str | None = None
) -> tuple[str, int | None]:
    """Never expose requests exceptions: the webhook URL is the credential."""
    first_id, delivered = None, 0
    parts = discord_parts(text)
    try:
        for n, content in enumerate(parts):
            payload = {"content": content, "allowed_mentions": {"parse": []}}
            if photo_url and n == len(parts) - 1:
                payload["embeds"] = [{"image": {"url": photo_url}}]
            response = requests.post(
                webhook, params={"wait": "true"}, json=payload, timeout=15
            )
            if response.status_code == 200:
                mid = response.json().get("id")
                if isinstance(mid, str) and mid.isdigit():
                    first_id = first_id or int(mid)
                    delivered += 1
                    if n < len(parts) - 1:
                        time.sleep(DISCORD_GAP)
                    continue
            if delivered:
                # Part of the message is already public: never resend the whole digest.
                failure_reason("Discord", "webhook", response.status_code, "partial digest")
                return "uncertain", first_id
            if response.status_code == 429:
                try:
                    delay = max(1, math.ceil(float(response.json().get("retry_after", 900))))
                except (ValueError, TypeError, AttributeError):
                    delay = 900
                return f"retry:{int(time.time()) + delay}", None
            failure_reason("Discord", "webhook", response.status_code, None)
            if 400 <= response.status_code < 500:
                return "rejected", None
            return "uncertain", None
        return "sent", first_id
    except (requests.RequestException, ValueError, AttributeError, TypeError) as exc:
        failure_reason("Discord", "request", None, type(exc).__name__)
    return "uncertain", first_id


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
        failure_reason("Telegram", method, response.status_code, data.get("description"))
        if 400 <= response.status_code < 500 and data.get("ok") is False:
            return "rejected", None
    except (requests.RequestException, ValueError, AttributeError, TypeError) as exc:
        failure_reason("Telegram", "request", None, type(exc).__name__)
    return "uncertain", None


# Ritmo: Telegram admite ~20 mensajes por minuto en un mismo canal y Discord ~30 por webhook.
# Los trabajos se intercalan entre canales, así el envío total dura lo que el canal más largo.
TELEGRAM_GAP = 3.1
DISCORD_GAP = 2.1
GLOBAL_GAP = 0.2
# Reclamaciones por lote: una escritura remota antes del lote y otra después, en vez de dos por
# mensaje (GitHub limita las escrituras de contenido a ~80/min y 500/h). Si el proceso muere a mitad
# de lote, sus mensajes quedan 'sending' y nunca se reenvían (se informan como dudosos).
BATCH = 25


def channel_jobs(channel: dict, books: list[dict], today: date, tag: str) -> list[dict]:
    """What a channel publishes today: one digest, or one message per book; weekly only on its day."""
    day = today.isoformat()
    mine = [
        b
        for b in books
        if not channel.get("categories")
        or set(b.get("categories", [])) & set(channel["categories"])
    ]
    label = channel.get("label", "")
    if channel.get("period") == "weekly":
        if today.weekday() != int(channel.get("weekday", 0)):
            return []
        until = today + timedelta(days=WEEK_DAYS - 1)
        week = [b for b in mine if day <= b["release_date"] <= until.isoformat()]
        summary = digest(week, day, tag, label, until=until.isoformat())
        return [summary] if summary else []
    due = [b for b in mine if b["release_date"] == day]
    if channel.get("mode") == "digest":
        summary = digest(due, day, tag, label)
        return [summary] if summary else []
    return due


def interleave(per_channel: list[tuple[dict, list[dict]]]) -> list[tuple[dict, dict]]:
    """Digests first, then book by book, alternating channels (round robin)."""
    digests = [(c, b) for c, items in per_channel for b in items if b.get("digest")]
    queues = [[(c, b) for b in items if not b.get("digest")] for c, items in per_channel]
    books = []
    while any(queues):
        for q in queues:
            if q:
                books.append(q.pop(0))
    return digests + books


def run(
    catalog: dict,
    today: date,
    db_path: Path,
    live: bool = False,
    tag: str = "",
    sender=send,
    checkpoint=None,
    discord_sender=send_discord,
    now: datetime | None = None,
    cover_resolver=None,
) -> list[dict]:
    if now is not None and now.time() < SEND_AT:
        return []  # Nothing goes out before 11:30 (Madrid); the 11:30 run sends the day.
    jobs = interleave(
        [(c, channel_jobs(c, catalog["books"], today, tag)) for c in catalog["channels"]]
    )
    if not live:
        return [
            {"chat_id": c["chat_id"], "status": "preview", "text": message(b, tag)}
            for c, b in jobs
        ]
    if catalog.get("demo", False):
        raise ValueError("Demo catalogs cannot send real messages")
    tokens = {
        c["token_env"]: os.environ.get(c["token_env"], "")
        for c in catalog["channels"]
        if c.get("platform") != "discord"
    }
    if not all(tokens.values()):
        raise ValueError("Configure all bot token environment variables before sending")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    results, sendable = [], []
    with closing(sqlite3.connect(db_path, timeout=30)) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS deliveries (chat TEXT, asin TEXT, status TEXT, message_id INTEGER, PRIMARY KEY(chat, asin))"
        )
        stale = False
        for channel, book in jobs:
            key = (channel["chat_id"], book["asin"])
            row = db.execute(
                "SELECT status FROM deliveries WHERE chat=? AND asin=?", key
            ).fetchone()
            if row and row[0].startswith("retry:") and time.time() >= int(
                row[0].split(":", 1)[1]
            ):
                db.execute("DELETE FROM deliveries WHERE chat=? AND asin=?", key)
                row = None
            if row and row[0] == "sending":
                # A claim left by an earlier cycle that died mid-send: the message may or may not have
                # gone out. Never resend; record it once as 'uncertain' (reported in this cycle) so later
                # cycles skip it quietly instead of staying red for the whole day.
                db.execute(
                    "UPDATE deliveries SET status='uncertain' WHERE chat=? AND asin=?", key
                )
                stale = True
                results.append(
                    {"chat_id": key[0], "asin": key[1], "status": "uncertain:stale-claim"}
                )
            elif row:
                results.append(
                    {"chat_id": key[0], "asin": key[1], "status": "skipped:" + row[0]}
                )
            else:
                sendable.append((channel, book))
        db.commit()
        if stale and checkpoint:
            checkpoint(db_path)
        last_chat, last_any = {}, 0.0
        blocked = set()
        for start in range(0, len(sendable), BATCH):
            batch = [
                (c, b) for c, b in sendable[start : start + BATCH] if c["chat_id"] not in blocked
            ]
            if not batch:
                continue
            # Commit the claims before HTTP. A crash leaves visible 'sending' rows,
            # which deliberately block automatic resends after an ambiguous delivery.
            db.execute("BEGIN IMMEDIATE")
            db.executemany(
                "INSERT INTO deliveries VALUES (?, ?, 'sending', NULL)",
                [(c["chat_id"], b["asin"]) for c, b in batch],
            )
            db.commit()
            if checkpoint:
                checkpoint(db_path)  # Must be durable remotely BEFORE the HTTP side effect.
            for channel, book in batch:
                key = (channel["chat_id"], book["asin"])
                if key[0] in blocked:
                    # The channel hit a rate limit earlier in this batch: release the claim
                    # (nothing was sent) so a later cycle sends it.
                    db.execute("DELETE FROM deliveries WHERE chat=? AND asin=?", key)
                    db.commit()
                    continue
                discord = channel.get("platform") == "discord"
                gap = DISCORD_GAP if discord else TELEGRAM_GAP
                wait = max(
                    last_chat.get(key[0], -1e9) + gap - time.monotonic(),
                    last_any + GLOBAL_GAP - time.monotonic(),
                )
                if wait > 0:
                    time.sleep(wait)
                photo = None if book.get("digest") else book.get("cover_url")
                if cover_resolver and not book.get("digest"):
                    photo = cover_resolver(book) or photo
                if discord:
                    status, mid = discord_sender(
                        channel["webhook"], key[0], message(book, tag), photo
                    )
                else:
                    status, mid = sender(
                        tokens[channel["token_env"]], key[0], message(book, tag), photo
                    )
                last_chat[key[0]] = last_any = time.monotonic()
                if status.startswith("retry:"):
                    blocked.add(key[0])
                db.execute(
                    "UPDATE deliveries SET status=?, message_id=? WHERE chat=? AND asin=?",
                    (status, mid, *key),
                )
                db.commit()
                results.append({"chat_id": key[0], "asin": key[1], "status": status})
            if checkpoint:
                checkpoint(db_path)
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

    def test_discord(webhook, chat_id, text, photo_url=None):
        return send_discord(webhook, chat_id, test_text(text), photo_url)

    results = run(
        test_catalog,
        date.fromisoformat(selected[0]["release_date"]),
        db_path,
        live,
        sender=test_sender,
        checkpoint=checkpoint,
        discord_sender=test_discord,
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
                now = None if args.date else datetime.now(ZoneInfo("Europe/Madrid"))
                results = run(catalog, today, db_path, args.send, now=now)
            print(json.dumps(results, ensure_ascii=False), flush=True)
            if not args.watch:
                if any(
                    r["status"].startswith(
                        (
                            "uncertain",
                            "rejected",
                            "retry",
                            "skipped:sending",
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
