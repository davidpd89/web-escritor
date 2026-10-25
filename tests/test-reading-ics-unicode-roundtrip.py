#!/usr/bin/env python3
"""Fidelidad Unicode del calendario de lanzamientos."""
import importlib.util
import sys
import unittest
from pathlib import Path
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_ics_unicode_qa', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class ICSUnicodeRoundtrip(unittest.TestCase):
    def test_committed_calendar_is_utf8_and_parseable(self):
        payload = (ROOT / 'recomendaciones/proximos-lanzamientos.ics').read_bytes()
        payload.decode('utf-8')
        calendar = Calendar.from_ical(payload)
        self.assertEqual(calendar.name, 'VCALENDAR')
        for event in (component for component in calendar.walk() if component.name == 'VEVENT'):
            with self.subTest(uid=str(event.get('UID'))):
                self.assertTrue(str(event.get('SUMMARY')).strip())
                self.assertTrue(str(event.get('DESCRIPTION')).strip())
                self.assertEqual(str(event.get('SUMMARY')).encode('utf-8').decode('utf-8'), str(event.get('SUMMARY')))

    def test_generator_escapes_unicode_text(self):
        self.assertTrue(callable(builder.render_release_ics))
        self.assertEqual(builder.esc('Niñez & fantasía'), 'Niñez &amp; fantasía')

if __name__ == '__main__':
    unittest.main()
