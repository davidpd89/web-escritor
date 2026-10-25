#!/usr/bin/env python3
"""Regresión temporal del RSS; sin red ni reloj del sistema."""
import importlib.util
import unittest
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_timezone_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedTimezoneNormalization(unittest.TestCase):
    def test_offsets_preserve_instant(self):
        samples = [
            '2026-10-25T00:30:00+02:00',
            '2026-10-25T23:45:00-05:00',
            '2026-03-29T01:30:00+01:00',
            '2026-03-29T03:30:00+02:00',
            '2026-10-25T01:30:00Z',
        ]
        for source in samples:
            with self.subTest(source=source):
                actual = feed.iso_to_rfc2822(source)
                self.assertIsNotNone(actual)
                parsed = parsedate_to_datetime(actual)
                expected = datetime.fromisoformat(source.replace('Z', '+00:00'))
                self.assertEqual(parsed.astimezone(timezone.utc), expected.astimezone(timezone.utc))
                self.assertEqual(parsed.utcoffset().total_seconds(), 0)
                self.assertEqual(parsed.strftime('%a'), parsed.strftime('%a, %d %b %Y %H:%M:%S %z')[:3])

if __name__ == '__main__':
    unittest.main()
