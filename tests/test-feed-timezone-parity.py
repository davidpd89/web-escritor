#!/usr/bin/env python3
"""Paridad temporal ISO 8601 -> RSS, sin red ni reloj real."""
import importlib.util
import unittest
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_timezone_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedTimezoneParity(unittest.TestCase):
    def test_offsets_preserve_instant(self):
        cases = [
            '2026-10-25T02:30:00+02:00',
            '2026-10-25T02:30:00+01:00',
            '2026-12-31T23:30:00-05:00',
            '2026-01-01T00:15:00+05:30',
            '2026-05-26T12:00:00Z',
        ]
        for source in cases:
            with self.subTest(source=source):
                expected = datetime.fromisoformat(source.replace('Z', '+00:00')).astimezone(timezone.utc)
                result = feed.iso_to_rfc2822(source)
                self.assertIsNotNone(result)
                actual = parsedate_to_datetime(result)
                self.assertIsNotNone(actual.tzinfo)
                self.assertEqual(actual.astimezone(timezone.utc), expected)

    def test_date_only_is_midnight_utc(self):
        result = feed.iso_to_rfc2822('2026-05-26')
        self.assertEqual(parsedate_to_datetime(result), datetime(2026, 5, 26, tzinfo=timezone.utc))

    def test_invalid_dates_do_not_generate_false_publication_dates(self):
        for value in ('2026-02-30', 'not-a-date', '', '2026-13-01'):
            with self.subTest(value=value):
                self.assertIsNone(feed.iso_to_rfc2822(value))

if __name__ == '__main__':
    unittest.main()
