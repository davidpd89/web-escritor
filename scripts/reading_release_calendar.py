#!/usr/bin/env python3
"""Preparar calendarios iCalendar a partir de fechas editoriales verificadas.

No se integra en el cron ni en las páginas públicas en esta PR.
Uso: python scripts/reading_release_calendar.py --preview
     python scripts/reading_release_calendar.py --out assets/reading-calendar
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://davidportodiaz.com"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
FULL_DAY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
FEED = "proximos-lanzamientos.ics"


def exact_day(raw):
    """Never turn a partial publication month or year into an invented day."""
    if not isinstance(raw, str) or not FULL_DAY.fullmatch(raw):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def ical_text(value):
    """RFC 5545 TEXT escape, including CR/LF to prevent field injection."""
    value = str(value).replace("\r\n", "\n").replace("\r", "\n")
    return (value.replace("\\", "\\\\").replace(";", r"\;")
            .replace(",", r"\,").replace("\n", r"\n"))


def fold(line):
    """Fold at <=75 UTF-8 octets, without splitting a Unicode character."""
    pieces, current = [], ""
    for char in line:
        if len((current + char).encode("utf-8")) > 75:
            if not current:
                raise ValueError("Carácter individual demasiado largo")
            pieces.append(current)
            current = " " + char
        else:
            current += char
    pieces.append(current)
    return "\r\n".join(pieces)


def release_books(catalogue, today, *, future_days=365, past_days=30):
    """Only publicly visible books with an exact editorial release date."""
    if future_days < 0 or past_days < 0:
        raise ValueError("Los horizontes no pueden ser negativos")
    chosen, seen = [], set()
    for book in catalogue["libros"]:
        if book.get("estado") != "publicado":
            continue
        release = exact_day(book.get("fecha_publicacion"))
        if release is None or not today - timedelta(days=past_days) <= release <= today + timedelta(days=future_days):
            continue
        ident, slug = book.get("id", ""), book.get("slug", "")
        if not isinstance(ident, str) or not SLUG.fullmatch(ident):
            raise ValueError("ID de libro inseguro")
        if not isinstance(slug, str) or not SLUG.fullmatch(slug):
            raise ValueError("Slug de libro inseguro")
        if ident in seen:
            raise ValueError("ID duplicado")
        if not book.get("titulo") or not book.get("autores"):
            raise ValueError("Libro sin título o autoría")
        stamp = exact_day(book.get("fecha_actualizacion")) or exact_day(book.get("fecha_verificacion"))
        if stamp is None:
            raise ValueError("Libro sin fecha de actualización verificable")
        seen.add(ident)
        chosen.append((release, ident, book, stamp))
    return sorted(chosen, key=lambda entry: (entry[0], entry[1]))


def event(entry):
    release, ident, book, stamp = entry
    authors = ", ".join(book["autores"])
    link = SITE + "/recomendaciones/libros/" + book["slug"] + "/"
    return [
        "BEGIN:VEVENT",
        "UID:lectura-" + ident + "@davidportodiaz.com",
        "DTSTAMP:" + stamp.strftime("%Y%m%dT000000Z"),
        "DTSTART;VALUE=DATE:" + release.strftime("%Y%m%d"),
        "DTEND;VALUE=DATE:" + (release + timedelta(days=1)).strftime("%Y%m%d"),
        "SUMMARY:" + ical_text("Lanzamiento: " + book["titulo"]),
        "DESCRIPTION:" + ical_text("De " + authors + ". Ficha: " + link),
        "URL:" + link,
        "TRANSP:TRANSPARENT",
        "END:VEVENT",
    ]


def calendar(entries):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//David Porto Diaz//Lanzamientos literarios//ES",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:" + ical_text("Próximos lanzamientos literarios"),
    ]
    for entry in entries:
        lines.extend(event(entry))
    lines.append("END:VCALENDAR")
    return ("\r\n".join(fold(line) for line in lines) + "\r\n").encode("utf-8")


def outputs(catalogue, today, *, future_days=365, past_days=30):
    releases = release_books(catalogue, today, future_days=future_days, past_days=past_days)
    files = {FEED: calendar(releases)}
    # The subscribed feed keeps recent releases briefly; standalone imports
    # are only offered while the title is genuinely upcoming.
    for entry in releases:
        if entry[0] > today:
            files[entry[1] + ".ics"] = calendar([entry])
    return files


def write_outputs(files, destination):
    """Dedicated generated namespace: remove stale files, nothing else."""
    destination.mkdir(parents=True, exist_ok=True)
    for path in destination.glob("*.ics"):
        if path.name in files:
            continue
        # Never delete unrelated personal calendars in a caller-supplied folder.
        if not path.name.startswith(("isbn-", "lib-")) or not path.is_file():
            continue
        if b"PRODID:-//David Porto Diaz//Lanzamientos literarios//ES" in path.read_bytes()[:2048]:
            path.unlink()
    for name, content in files.items():
        target = destination / name
        if not target.is_file() or target.read_bytes() != content:
            target.write_bytes(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=ROOT / "data/reading-catalogue.json")
    parser.add_argument("--today", help="YYYY-MM-DD; por defecto día civil Europe/Madrid")
    parser.add_argument("--future-days", type=int, default=365)
    parser.add_argument("--past-days", type=int, default=30)
    parser.add_argument("--out", type=Path, help="Directorio exclusivo de salida")
    parser.add_argument("--preview", action="store_true", help="Solo informar, sin escribir")
    args = parser.parse_args()
    today = exact_day(args.today) if args.today else datetime.now(ZoneInfo("Europe/Madrid")).date()
    if today is None:
        parser.error("--today debe ser una fecha ISO completa")
    catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
    files = outputs(catalogue, today, future_days=args.future_days, past_days=args.past_days)
    if not args.preview:
        if args.out is None:
            parser.error("Se requiere --out, o utiliza --preview")
        write_outputs(files, args.out)
    print(json.dumps({
        "dia_madrid": today.isoformat(), "modo": "solo_vista_previa" if args.preview else "archivos_generados",
        "eventos_proximos": len(files) - 1, "archivos": sorted(files),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
