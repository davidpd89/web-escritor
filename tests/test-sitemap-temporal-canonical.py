import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_temporal', ROOT / 'scripts/build-sitemap.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SitemapTemporalTests(unittest.TestCase):
    def test_equivalent_instants(self):
        cases = [
            '2026-06-30T22:30:00Z',
            '2026-07-01T00:30:00+02:00',
            '2026-06-30T18:30:00-04:00',
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertEqual(mod.normalize_lastmod(value),
                    '2026-06-30T22:30:00Z')

    def test_reject_impossible_civil_dates(self):
        for value in ('2026-02-29', '2026-04-31', '2026-13-01', '2026-00-10'):
            with self.subTest(value=value):
                self.assertIsNone(mod.normalize_lastmod(value))

    def test_preserve_valid_date_precision(self):
        self.assertEqual(mod.normalize_lastmod('2028-02-29'), '2028-02-29')
        self.assertEqual(mod.normalize_lastmod('2026-10-24'), '2026-10-24')

if __name__ == '__main__':
    unittest.main()
