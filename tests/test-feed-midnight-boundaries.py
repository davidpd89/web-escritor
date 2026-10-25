#!/usr/bin/env python3
"""Límites UTC del calendario RSS."""
import importlib.util
import unittest
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_midnight_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class MidnightBoundaries(unittest.TestCase):
    def test_previous_utc_day(self):
        actual = parsedate_to_datetime(feed.iso_to_rfc2822('2026-10-25T00:30:00+02:00'))
        self.assertEqual(actual.strftime('%Y-%m-%d %H:%M'), '2026-10-24 22:30')
        self.assertEqual(actual.strftime('%a'), 'Sat')

    def test_next_utc_day(self):
        actual = parsedate_to_datetime(feed.iso_to_rfc2822('2026-10-25T23:30:00-03:00'))
        self.assertEqual(actual.strftime('%Y-%m-%d %H:%M'), '2026-10-26 02:30')
        self.assertEqual(actual.strftime('%a'), 'Mon')

if __name__ == '__main__':
    unittest.main()
