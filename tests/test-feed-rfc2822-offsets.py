import importlib.util
import unittest
from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_offsets', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedOffsetTests(unittest.TestCase):
    def test_equivalent_instants(self):
        expected = datetime(2026, 6, 30, 22, 30, tzinfo=timezone.utc)
        inputs = [
            '2026-06-30T22:30:00Z',
            '2026-07-01T00:30:00+02:00',
            '2026-06-30T18:30:00-04:00',
            '2026-07-01T07:30:00+09:00',
        ]
        for raw in inputs:
            with self.subTest(raw=raw):
                actual = feed.iso_to_rfc2822(raw)
                self.assertIsNotNone(actual)
                parsed = parsedate_to_datetime(actual)
                self.assertEqual(parsed.astimezone(timezone.utc), expected)
                self.assertEqual(parsed.utcoffset().total_seconds(), 0)
                self.assertEqual(actual[:3], 'Tue')

    def test_no_invented_date_for_bad_input(self):
        for raw in ('2026-02-30', 'no-date', '2026-13-01'):
            with self.subTest(raw=raw):
                self.assertFalse(feed.iso_to_rfc2822(raw))

if __name__ == '__main__':
    unittest.main()
