#!/usr/bin/env python3
"""Integridad temporal de los lanzamientos ICS. Sin red ni reloj."""
from __future__ import annotations

import unittest
from datetime import date, datetime
from pathlib import Path
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
ICS = ROOT / 'recomendaciones/proximos-lanzamientos.ics'


class TemporalIntegrity(unittest.TestCase):
    def test_ics_event_temporal_contract(self):
        calendar = Calendar.from_ical(ICS.read_bytes())
        self.assertEqual(str(calendar.get('VERSION')), '2.0')
        events = [component for component in calendar.walk() if component.name == 'VEVENT']
        uids = []
        for event in events:
            uid = str(event.get('UID', ''))
            with self.subTest(uid=uid):
                self.assertTrue(uid)
                self.assertIn('DTSTART', event)
                self.assertIn('DTEND', event)
                start = event.decoded('DTSTART')
                end = event.decoded('DTEND')
                self.assertEqual(isinstance(start, datetime), isinstance(end, datetime))
                self.assertIsInstance(start, date)
                self.assertIsInstance(end, date)
                if isinstance(start, datetime):
                    self.assertEqual(start.tzinfo is None, end.tzinfo is None)
                self.assertGreater(end, start)
                self.assertTrue(str(event.get('SUMMARY', '')).strip())
                uids.append(uid)
        self.assertEqual(len(uids), len(set(uids)))


if __name__ == '__main__':
    unittest.main()
