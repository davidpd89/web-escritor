#!/usr/bin/env python3
"""Integridad estructural del calendario ICS de recomendaciones."""
import unittest
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
ICS = ROOT / 'recomendaciones/proximos-lanzamientos.ics'

class ReleaseIcsStructure(unittest.TestCase):
    def test_calendar_is_valid_and_events_have_stable_identity(self):
        self.assertTrue(ICS.is_file())
        calendar = Calendar.from_ical(ICS.read_bytes())
        events = [component for component in calendar.walk() if component.name == 'VEVENT']
        self.assertTrue(events, 'El calendario debe contener lanzamientos')
        seen = set()
        for event in events:
            uid = str(event.get('UID', ''))
            with self.subTest(uid=uid):
                self.assertTrue(uid.endswith('@davidportodiaz.com'))
                self.assertNotIn(uid, seen)
                seen.add(uid)
                start = event.get('DTSTART')
                self.assertIsNotNone(start)
                self.assertIs(type(start.dt), date, 'El lanzamiento debe ser un evento de día completo')
                self.assertNotIsInstance(start.dt, datetime)
                self.assertTrue(str(event.get('SUMMARY', '')).startswith('Sale a la venta: '))
                url = str(event.get('URL', ''))
                parsed = urlparse(url)
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(parsed.hostname, 'davidportodiaz.com')
                self.assertTrue(parsed.path.startswith('/recomendaciones/libros/'))
                self.assertTrue(parsed.path.endswith('/'))
                self.assertFalse(parsed.query)
                self.assertFalse(parsed.fragment)

if __name__ == '__main__':
    unittest.main()
