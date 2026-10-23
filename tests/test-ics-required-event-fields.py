#!/usr/bin/env python3
"""Independent RFC 5545 event contracts shared by release and radar calendars.

icalendar accepts VEVENT records that omit mandatory fields, so a successful
parse alone (the older round-trip test) does not prove RFC conformance.
All checks run offline and use the committed generated_for date, not now().
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_required_events(payload: bytes) -> dict[str, object]:
    """Check required fields before accepting the permissive external parser."""
    assert payload.startswith(b"BEGIN:VCALENDAR\r\n"), "Not an iCalendar document"
    assert payload.endswith(b"END:VCALENDAR\r\n"), "Calendar must end with CRLF"
    assert b"\n" not in payload.replace(b"\r\n", b""), "Bare LF is not a valid ICS line ending"
    assert all(len(line) <= 75 for line in payload.split(b"\r\n")), "RFC 5545 line exceeds 75 octets"
    parsed = Calendar.from_ical(payload)
    records = [component for component in parsed.walk() if component.name == "VEVENT"]
    by_uid = {}
    for event in records:
        for property_name in ("UID", "DTSTAMP", "DTSTART", "DTEND", "SUMMARY"):
            assert event.get(property_name) is not None, f"VEVENT missing {property_name}"
        uid = str(event.get("UID"))
        assert uid not in by_uid, f"Duplicate calendar UID: {uid}"
        by_uid[uid] = event
        stamp = event.get("DTSTAMP").dt
        assert isinstance(stamp, datetime) and stamp.tzinfo is not None, f"Bad UTC DTSTAMP: {uid}"
        assert stamp.utcoffset() == timedelta(0), f"Non-UTC DTSTAMP: {uid}"
        start, end = event.get("DTSTART").dt, event.get("DTEND").dt
        assert isinstance(start, date) and not isinstance(start, datetime), f"Not an all-day event: {uid}"
        assert end == start + timedelta(days=1), f"All-day end is not exclusive: {uid}"
    return by_uid


class CalendarContract(unittest.TestCase):
    def test_radar_ics_matches_public_json_and_source_verification(self):
        source = json.loads((ROOT / "data/radar-opportunities.json").read_text(encoding="utf-8"))
        public = json.loads((ROOT / "convocatorias-escritores/opportunities.json").read_text(encoding="utf-8"))
        blob = (ROOT / "convocatorias-escritores/deadlines.ics").read_bytes()
        events = parse_required_events(blob)
        by_id = {row["id"]: row for row in source["items"]}
        expected = {row["id"] + "@davidportodiaz.com": row for row in public["items"]}
        self.assertEqual(set(events), set(expected), "ICS, public JSON and displayed open items must agree")
        for uid, event in events.items():
            item = expected[uid]
            original = by_id[item["id"]]
            self.assertEqual(event.get("DTSTART").dt, date.fromisoformat(item["deadline"]), uid)
            self.assertEqual(event.get("DTSTAMP").dt,
                             datetime.combine(date.fromisoformat(original["verified_at"]), datetime.min.time(), timezone.utc), uid)
            self.assertEqual(str(event.get("SUMMARY")), item["title"], uid)
            self.assertEqual(str(event.get("DESCRIPTION")), item["organizer"], uid)
            self.assertEqual(str(event.get("URL")), item["source_url"], uid)
        builder = load_script("radar_ics_contract_builder", "build-radar-opportunities.py")
        self.assertEqual(blob, builder.build_ics(builder.load_items(ROOT / "data/radar-opportunities.json"),
                                               date.fromisoformat(public["generated_for"])).encode("utf-8"),
                         "Radar .ics must match the generator, not just parse successfully")

    def test_releases_ics_required_properties_and_published_editions(self):
        blob = (ROOT / "recomendaciones/proximos-lanzamientos.ics").read_bytes()
        events = parse_required_events(blob)
        catalogue = json.loads((ROOT / "data/reading-catalogue.json").read_text(encoding="utf-8"))
        published = {b["id"]: b for b in catalogue["libros"] if b["estado"] == "publicado"}
        for uid, event in events.items():
            self.assertTrue(uid.endswith("@davidportodiaz.com"))
            book_id = uid.removesuffix("@davidportodiaz.com")
            self.assertIn(book_id, published, uid)
            book = published[book_id]
            self.assertEqual(event.get("DTSTART").dt, date.fromisoformat(book["fecha_publicacion"]), uid)
            self.assertEqual(str(event.get("SUMMARY")), "Sale a la venta: " + book["titulo"], uid)
            self.assertIn("/recomendaciones/libros/", str(event.get("URL")), uid)

    def test_both_generators_normalize_crlf_and_bare_cr_in_source_text(self):
        radar = load_script("radar_ics_text", "build-radar-opportunities.py")
        reading = load_script("reading_ics_text", "build-reading-catalogue.py")
        for escape in (radar.ics_escape, reading.ics_text):
            with self.subTest(generator=escape.__name__):
                for raw in ("A\rB", "A\r\nB", "A\nB"):
                    encoded = escape(raw)
                    self.assertEqual(encoded, r"A\nB")
                    self.assertNotIn("\r", encoded)
                    self.assertNotIn("\n", encoded)
                self.assertEqual(escape("A,B;C"), r"A\,B\;C")

    def test_independent_parser_alone_is_not_a_sufficient_contract(self):
        radar = (ROOT / "convocatorias-escritores/deadlines.ics").read_bytes()
        self.assertIn(b"DTSTAMP:", radar)
        broken = radar.replace(b"DTSTAMP:", b"X-MISSING:", 1)
        # The third-party parser can still read the broken record. Our
        # explicit VEVENT contract must reject it.
        self.assertGreater(len([x for x in Calendar.from_ical(broken).walk() if x.name == "VEVENT"]), 0)
        with self.assertRaisesRegex(AssertionError, "missing DTSTAMP"):
            parse_required_events(broken)


if __name__ == "__main__":
    unittest.main()
