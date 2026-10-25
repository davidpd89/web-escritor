import importlib.util
import unittest
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rss_timezone', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RssTimezoneParity(unittest.TestCase):
    def test_equivalent_instants_produce_identical_pubdate(self):
        variants = [
            '2026-10-25T00:30:00+02:00',
            '2026-10-24T22:30:00Z',
            '2026-10-24T17:30:00-05:00',
        ]
        outputs = [mod.iso_to_rfc2822(value) for value in variants]
        self.assertEqual(len(set(outputs)), 1)
        self.assertEqual(outputs[0], 'Sat, 24 Oct 2026 22:30:00 +0000')

    def test_pubdate_roundtrips_to_original_instant(self):
        for value in ('2026-06-10T19:00:00+02:00', '2026-12-31T23:30:00-03:00'):
            with self.subTest(value=value):
                output = mod.iso_to_rfc2822(value)
                self.assertIsNotNone(output)
                actual = parsedate_to_datetime(output)
                expected = datetime.fromisoformat(value).astimezone(timezone.utc)
                self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()
