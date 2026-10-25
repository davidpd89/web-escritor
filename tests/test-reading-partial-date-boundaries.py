import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_partial_dates', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PartialDateBoundaries(unittest.TestCase):
    def test_calendar_months(self):
        for month in range(1, 13):
            with self.subTest(month=month):
                self.assertEqual(mod.day(f'2026-{month:02d}-01', 'fecha').month, month)

    def test_impossible_months(self):
        for value in ['2026-00-01', '2026-13-01', '2026-99-01', '2026-1-01', '2026-02-30', '2025-02-29', '2026-12-00']:
            with self.subTest(value=value):
                with self.assertRaises(mod.ValidationError):
                    mod.day(value, 'fecha')

if __name__ == '__main__':
    unittest.main()