#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build-event-calendars.py"
SPEC = importlib.util.spec_from_file_location("build_event_calendars", MODULE_PATH)
assert SPEC and SPEC.loader
cal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cal)


def page_for(event: dict, *, include_link: bool = True) -> str:
    fragment = event["@id"].split("#", 1)[1]
    link = ""
    if include_link:
        link = (
            f'<a href="/assets/events/calendar/{fragment}.ics" '
            'data-calendar-download>Añadir al calendario</a>'
        )
    payload = {"@context": "https://schema.org", "@graph": [event]}
    return (
        '<!doctype html><html><head><script type="application/ld+json">'
        + json.dumps(payload, ensure_ascii=False)
        + "</script></head><body>"
        + link
        + "</body></html>"
    )


class EventCalendarTests(unittest.TestCase):
    def timed_event(self) -> dict:
        return {
            "@type": "Event",
            "@id": "https://davidportodiaz.com/eventos.html#presentacion-manecillas",
            "name": "Presentación: Las manecillas del recuerdo",
            "description": "Encuentro, firma; preguntas y línea larga con tildes áéíóú " * 3,
            "startDate": "2026-09-10T19:00:00+02:00",
            "endDate": "2026-09-10T20:30:00+02:00",
            "dateModified": "2026-08-23",
            "eventStatus": cal.EVENT_SCHEDULED,
            "url": "https://davidportodiaz.com/eventos.html#presentacion-manecillas",
            "location": {
                "@type": "Place",
                "name": "Librería Ñ",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "Calle Mayor, 1",
                    "postalCode": "28013",
                    "addressLocality": "Madrid",
                    "addressCountry": "ES",
                },
            },
        }

    def test_timed_event_is_normalized_to_utc_and_folded(self) -> None:
        generated = cal.build_ics(self.timed_event())
        text = generated.decode("utf-8")
        self.assertIn("DTSTART:20260910T170000Z\r\n", text)
        self.assertIn("DTEND:20260910T183000Z\r\n", text)
        self.assertIn("DTSTAMP:20260823T000000Z\r\n", text)
        self.assertIn("SUMMARY:Presentación: Las manecillas del recuerdo", text)
        self.assertIn("LOCATION:Librería Ñ\\, Calle Mayor\\, 1\\, 28013\\, Madrid\\, ES", text.replace("\r\n ", ""))
        self.assertTrue(generated.endswith(b"\r\n"))
        for physical in generated.split(b"\r\n"):
            self.assertLessEqual(len(physical), 75)

    def test_all_day_event_uses_exclusive_ical_end_date(self) -> None:
        event = self.timed_event()
        event["startDate"] = "2026-09-10"
        event["endDate"] = "2026-09-10"
        generated = cal.build_ics(event).decode("utf-8")
        self.assertIn("DTSTART;VALUE=DATE:20260910\r\n", generated)
        self.assertIn("DTEND;VALUE=DATE:20260911\r\n", generated)

    def test_completed_event_creates_no_calendar(self) -> None:
        event = self.timed_event()
        event["eventStatus"] = cal.EVENT_COMPLETED
        expected, errors = cal.expected_calendars(page_for(event, include_link=False))
        self.assertEqual(expected, {})
        self.assertEqual(errors, [])

    def test_scheduled_event_requires_visible_calendar_link(self) -> None:
        event = self.timed_event()
        expected, errors = cal.expected_calendars(page_for(event, include_link=False))
        self.assertIn("presentacion-manecillas.ics", expected)
        self.assertEqual(len(errors), 1)
        self.assertIn("no tiene enlace visible", errors[0])

    def test_check_detects_missing_stale_and_orphan_files(self) -> None:
        event = self.timed_event()
        expected, errors = cal.expected_calendars(page_for(event))
        self.assertEqual(errors, [])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            missing = cal.check_outputs(expected, output)
            self.assertEqual(len(missing), 1)
            cal.write_outputs(expected, output)
            self.assertEqual(cal.check_outputs(expected, output), [])
            path = output / "presentacion-manecillas.ics"
            path.write_text("stale", encoding="utf-8")
            stale = cal.check_outputs(expected, output)
            self.assertEqual(len(stale), 1)
            cal.write_outputs(expected, output)
            (output / "huerfano.ics").write_text("orphan", encoding="utf-8")
            orphan = cal.check_outputs(expected, output)
            self.assertEqual(len(orphan), 1)
            self.assertIn("huerfano", orphan[0])

    def test_datetime_without_offset_is_rejected(self) -> None:
        event = self.timed_event()
        event["startDate"] = "2026-09-10T19:00:00"
        with self.assertRaisesRegex(ValueError, "offset"):
            cal.build_ics(event)


if __name__ == "__main__":
    unittest.main()
