import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_dates', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SitemapDateBoundaries(unittest.TestCase):
    def test_impossible_dates_are_rejected(self):
        for value in ('2026-02-30', '2026-13-01', '2025-02-29', '2026-00-12', '2026-04-31'):
            with self.subTest(value=value):
                self.assertIsNone(module.normalize_lastmod(value))

    def test_valid_leap_day(self):
        self.assertEqual(module.normalize_lastmod('2024-02-29'), '2024-02-29')

    def test_invalid_datetime(self):
        for value in ('2026-02-30T12:00:00Z', '2026-10-25T25:00:00Z'):
            with self.subTest(value=value):
                self.assertIsNone(module.normalize_lastmod(value))

if __name__ == '__main__':
    unittest.main()
