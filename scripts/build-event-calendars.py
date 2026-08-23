#!/usr/bin/env python3
"""Generate .ics files for scheduled events declared in eventos.html.

The JSON-LD Event nodes are the single source of truth. Only EventScheduled
nodes produce calendar files; completed/cancelled events are ignored.

Usage:
    python scripts/build-event-calendars.py
    python scripts/build-event-calendars.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, time, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "eventos.html"
DEFAULT_OUTPUT_DIR = ROOT / "assets" / "events" / "calendar"
EVENT_SCHEDULED = "https://schema.org/EventScheduled"
EVENT_COMPLETED = "https://schema.org/EventCompleted"
EVENT_CANCELLED = "https://schema.org/EventCancelled"


class JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._capture = False
        self._parts: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        values = {key.lower(): value for key, value in attrs}
        if (values.get("type") or "").lower() == "application/ld+json":
            self._capture = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._capture:
            self.blocks.append("".join(self._parts))
            self._capture = False
            self._parts = []


def _types(node: dict) -> set[str]:
    raw = node.get("@type")
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {value for value in raw if isinstance(value, str)}
    return set()


def _walk_json(value) -> Iterable[dict]:
    if isinstance(value, dict):
        if "Event" in _types(value):
            yield value
        for nested in value.values():
            yield from _walk_json(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_json(nested)


def extract_events(html_text: str) -> list[dict]:
    parser = JsonLdParser()
    parser.feed(html_text)
    events: list[dict] = []
    for block in parser.blocks:
        try:
            payload = json.loads(block)
        except json.JSONDecodeError:
            continue
        events.extend(_walk_json(payload))
    return events


def _event_fragment(event: dict) -> str:
    event_id = event.get("@id")
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError("EventScheduled sin @id")
    fragment = urlsplit(event_id).fragment
    if not fragment or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._~-]*", fragment):
        raise ValueError(f"@id de EventScheduled sin fragmento utilizable: {event_id!r}")
    return fragment


def _is_date_only(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def _parse_datetime(value: str, field: str) -> datetime:
    if not re.search(r"(?:Z|[+-]\d{2}:\d{2})$", value):
        raise ValueError(f"{field} DATE-TIME exige offset o Z: {value!r}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} invalido: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} DATE-TIME exige zona/offset")
    return parsed.astimezone(timezone.utc)


def _ical_datetime(value: str, field: str) -> str:
    return _parse_datetime(value, field).strftime("%Y%m%dT%H%M%SZ")


def _stable_dtstamp(event: dict) -> str:
    raw = event.get("dateModified") or event.get("startDate")
    if not isinstance(raw, str) or not raw:
        raise ValueError("EventScheduled sin dateModified/startDate para DTSTAMP estable")
    if _is_date_only(raw):
        parsed = date.fromisoformat(raw)
        return datetime.combine(parsed, time.min, tzinfo=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return _ical_datetime(raw, "dateModified/startDate")


def _escape_text(value: object) -> str:
    text = str(value or "")
    text = text.replace("\\", "\\\\")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", "\\n")
    return text.replace(";", "\\;").replace(",", "\\,")


def _fold_line(line: str) -> list[str]:
    if len(line.encode("utf-8")) <= 75:
        return [line]
    chunks: list[str] = []
    current = ""
    limit = 75
    for char in line:
        candidate = current + char
        if current and len(candidate.encode("utf-8")) > limit:
            chunks.append(current)
            current = char
            limit = 74  # continuation line includes one leading space
        else:
            current = candidate
    if current:
        chunks.append(current)
    return [chunks[0], *[" " + chunk for chunk in chunks[1:]]]


def _render_ical(lines: list[str]) -> bytes:
    physical: list[str] = []
    for line in lines:
        physical.extend(_fold_line(line))
    return ("\r\n".join(physical) + "\r\n").encode("utf-8")


def _location_text(event: dict) -> str:
    location = event.get("location")
    if not isinstance(location, dict):
        return ""
    parts: list[str] = []
    name = location.get("name")
    if isinstance(name, str) and name.strip():
        parts.append(name.strip())
    address = location.get("address")
    if isinstance(address, str) and address.strip():
        parts.append(address.strip())
    elif isinstance(address, dict):
        for field in ("streetAddress", "postalCode", "addressLocality", "addressRegion", "addressCountry"):
            value = address.get(field)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
    return ", ".join(parts)


def _event_times(event: dict) -> list[str]:
    start = event.get("startDate")
    end = event.get("endDate")
    if not isinstance(start, str) or not start:
        raise ValueError("EventScheduled sin startDate")

    if _is_date_only(start):
        start_date = date.fromisoformat(start)
        if end:
            if not isinstance(end, str) or not _is_date_only(end):
                raise ValueError("endDate debe ser DATE cuando startDate es DATE")
            end_date = date.fromisoformat(end)
            if end_date < start_date:
                raise ValueError("endDate anterior a startDate")
            end_exclusive = end_date + timedelta(days=1)
        else:
            end_exclusive = start_date + timedelta(days=1)
        return [
            f"DTSTART;VALUE=DATE:{start_date.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{end_exclusive.strftime('%Y%m%d')}",
        ]

    start_dt = _parse_datetime(start, "startDate")
    lines = [f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%SZ')}"]
    if end:
        if not isinstance(end, str) or _is_date_only(end):
            raise ValueError("endDate debe ser DATE-TIME cuando startDate es DATE-TIME")
        end_dt = _parse_datetime(end, "endDate")
        if end_dt < start_dt:
            raise ValueError("endDate anterior a startDate")
        lines.append(f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%SZ')}")
    return lines


def build_ics(event: dict) -> bytes:
    event_id = str(event.get("@id") or "")
    fragment = _event_fragment(event)
    name = event.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"EventScheduled {fragment!r} sin name")

    uid = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:32] + "@davidportodiaz.com"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//David Porto Diaz//Agenda//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{_stable_dtstamp(event)}",
        *_event_times(event),
        f"SUMMARY:{_escape_text(name.strip())}",
    ]
    description = event.get("description")
    if isinstance(description, str) and description.strip():
        lines.append(f"DESCRIPTION:{_escape_text(description.strip())}")
    location = _location_text(event)
    if location:
        lines.append(f"LOCATION:{_escape_text(location)}")
    url = event.get("url") or event_id
    if isinstance(url, str) and url.strip():
        lines.append(f"URL:{url.strip()}")
    lines.extend(["STATUS:CONFIRMED", "END:VEVENT", "END:VCALENDAR"])
    return _render_ical(lines)


class CalendarLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        values = {key.lower(): value for key, value in attrs}
        if "data-calendar-download" in values and values.get("href"):
            self.links.add(str(values["href"]))


def _calendar_links(html_text: str) -> set[str]:
    parser = CalendarLinkParser()
    parser.feed(html_text)
    return parser.links


def expected_calendars(html_text: str) -> tuple[dict[str, bytes], list[str]]:
    expected: dict[str, bytes] = {}
    errors: list[str] = []
    links = _calendar_links(html_text)
    for event in extract_events(html_text):
        if event.get("eventStatus") != EVENT_SCHEDULED:
            continue
        try:
            fragment = _event_fragment(event)
            filename = f"{fragment}.ics"
            href = f"/assets/events/calendar/{filename}"
            if filename in expected:
                raise ValueError(f"fragmento de evento duplicado: {fragment}")
            expected[filename] = build_ics(event)
            if href not in links:
                errors.append(
                    f"EventScheduled {fragment!r} no tiene enlace visible {href!r} con data-calendar-download"
                )
        except ValueError as exc:
            errors.append(str(exc))
    return expected, errors


def check_outputs(expected: dict[str, bytes], output_dir: Path) -> list[str]:
    errors: list[str] = []
    existing = {path.name: path for path in output_dir.glob("*.ics")} if output_dir.is_dir() else {}
    for filename, generated in expected.items():
        path = existing.get(filename)
        if path is None:
            errors.append(f"falta {output_dir / filename}")
        elif path.read_bytes() != generated:
            errors.append(f"{output_dir / filename} no coincide con el Event JSON-LD actual")
    for filename in sorted(existing.keys() - expected.keys()):
        errors.append(f"ICS huerfano: {existing[filename]}")
    return errors


def write_outputs(expected: dict[str, bytes], output_dir: Path) -> None:
    if expected:
        output_dir.mkdir(parents=True, exist_ok=True)
    if output_dir.is_dir():
        for path in output_dir.glob("*.ics"):
            if path.name not in expected:
                path.unlink()
    for filename, content in expected.items():
        (output_dir / filename).write_bytes(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="comprueba .ics y enlaces sin escribir")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    if not args.source.is_file():
        print(f"ERROR: no existe {args.source}", file=sys.stderr)
        return 1

    html_text = args.source.read_text(encoding="utf-8")
    expected, errors = expected_calendars(html_text)
    if args.check:
        errors.extend(check_outputs(expected, args.output_dir))
    elif not errors:
        write_outputs(expected, args.output_dir)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    action = "comprobados" if args.check else "generados"
    print(f"Calendarios {action}: {len(expected)} EventScheduled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
