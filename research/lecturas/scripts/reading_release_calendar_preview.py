#!/usr/bin/env python3
"""Offline iCalendar export for UPCOMING PUBLISHED book editions of our catalogue.

Separate, opt-in preview: does not change the site, cron, Pinterest or Amazon.
Only exact edition dates. One .ics per edition + an aggregate subscription feed.
A calendar client may choose how to handle VALARM; no email/push is sent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ISBN = re.compile(r"^97[89][0-9]{10}$")
SITE = "https://davidportodiaz.com"


def exact_date(value: object) -> date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def escape(value: str) -> str:
    # RFC 5545 TEXT values: never allow arbitrary line/property injection.
    return (str(value).replace("\r\n", "\n").replace("\r", "\n")
            .replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def fold(line: str) -> str:
    """Fold at 75 UTF-8 OCTETS (not characters), using CRLF + one space."""
    pieces, current, count = [], "", 0
    for character in line:
        width = len(character.encode("utf-8"))
        if count + width > 75:
            pieces.append(current)
            current = " "
            count = 1
        current += character
        count += width
    pieces.append(current)
    return "\r\n".join(pieces)


def event_rows(book: dict, today: date, *, horizon_days: int = 365) -> dict | None:
    if not isinstance(book, dict) or book.get("estado") != "publicado":
        return None
    publication = exact_date(book.get("fecha_publicacion"))
    # Year-only or month-only date is not an event. Confirm edition precision.
    if not publication or not 0 < (publication - today).days <= horizon_days:
        return None
    if book.get("precision_fecha") not in (None, "dia"):
        return None
    slug = book.get("slug")
    isbn = book.get("isbn13")
    if not isinstance(slug, str) or not SLUG.fullmatch(slug):
        return None
    if not isinstance(isbn, str) or not ISBN.fullmatch(isbn):
        return None
    if not book.get("titulo") or not book.get("autores"):
        return None
    page = SITE + "/recomendaciones/libros/" + slug + "/"
    digest = hashlib.sha256(("isbn:" + isbn).encode("utf-8")).hexdigest()[:20]
    return {
        "id": str(book["id"]), "slug": slug, "isbn": isbn,
        "start": publication,
        "end": publication + timedelta(days=1),
        "revision_day": exact_date(book.get("fecha_actualizacion")) or today,
        "url": page,
        "uid": f"lanzamiento-{digest}@davidportodiaz.com",
        "title": f"Lanzamiento: {book['titulo']}",
        "description": "Fecha de edición indicada por la editorial. Ficha del libro: " + page,
    }


def entries(books: list[dict], today: date, *, limit: int = 100) -> list[dict]:
    if not 1 <= limit <= 100:
        raise ValueError("El calendario admite hasta 100 lanzamientos")
    seen: set[str] = set()
    events = []
    for book in books:
        row = event_rows(book, today)
        if row is None:
            continue
        if row["isbn"] in seen:
            raise ValueError("Dos fichas del mismo ISBN exacto: " + row["isbn"])
        seen.add(row["isbn"])
        events.append(row)
    return sorted(events, key=lambda r: (r["start"], r["isbn"]))[:limit]


def calendar(rows: list[dict], *, generated_day: date) -> str:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//DavidPorto//Lanzamientos literarios//ES",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "X-WR-CALNAME:Lanzamientos de libros - David Porto"]
    for item in rows:
        # Avoid generating a new DTSTAMP every day when a book didn't change;
        # this reduces needless refreshes in subscribing calendar clients.
        stamp = item.get("revision_day", generated_day).strftime("%Y%m%d") + "T120000Z"
        lines.extend([
            "BEGIN:VEVENT", "UID:" + item["uid"], "DTSTAMP:" + stamp,
            "DTSTART;VALUE=DATE:" + item["start"].strftime("%Y%m%d"),
            "DTEND;VALUE=DATE:" + item["end"].strftime("%Y%m%d"),
            "SUMMARY:" + escape(item["title"]),
            "DESCRIPTION:" + escape(item["description"]),
            "URL:" + item["url"],
            "STATUS:CONFIRMED",
            "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY",
            "DESCRIPTION:" + escape(item["title"]), "END:VALARM",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"


def google_link(row: dict) -> str:
    return "https://calendar.google.com/calendar/render?" + urlencode({
        "action": "TEMPLATE", "text": row["title"],
        "dates": row["start"].strftime("%Y%m%d") + "/" + row["end"].strftime("%Y%m%d"),
        "details": row["description"], "location": row["url"],
    })


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue", type=Path, required=True)
    p.add_argument("--today", type=date.fromisoformat, required=True,
                   help="Fecha civil Madrid YYYY-MM-DD, no reloj UTC")
    p.add_argument("--out", type=Path, required=True,
                   help="Directorio de PREVIEW nuevo, no web publicada")
    args = p.parse_args()
    if args.out.exists():
        p.error("La carpeta ya existe; no sobrescribir publicación o manifiestos")
    raw = json.loads(args.catalogue.read_text(encoding="utf-8"))
    if raw.get("schema_version") != 1 or not isinstance(raw.get("libros"), list):
        p.error("Formato real de data/reading-catalogue.json no reconocido")
    found = entries(raw["libros"], args.today)
    args.out.mkdir(parents=True)
    (args.out / "lanzamientos.ics").write_bytes(
        calendar(found, generated_day=args.today).encode("utf-8"))
    manifest = []
    for item in found:
        name = "libro-" + item["isbn"] + ".ics"
        (args.out / name).write_bytes(calendar([item], generated_day=args.today).encode("utf-8"))
        manifest.append({"book_id": item["id"], "date": item["start"].isoformat(),
                         "ical_file": name, "google_calendar_url": google_link(item),
                         "canonical_book_url": item["url"]})
    (args.out / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "preview": True, "items": manifest},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"planned_calendar_entries": len(found), "preview": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
