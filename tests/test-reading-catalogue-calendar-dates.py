#!/usr/bin/env python3
"""Fechas bibliográficas y años bisiestos."""
import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_dates_qa', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class CatalogueDates(unittest.TestCase):
    def test_valid_dates(self):
        for value in ('2024-02-29', '2026-10-25', '2000-02-29'):
            with self.subTest(value=value):
                self.assertEqual(builder.day(value, 'fecha'), date.fromisoformat(value))

    def test_invalid_dates(self):
        for value in ('2026-02-29', '1900-02-29', '2026-04-31', '2026-13-01', '2026-1-01', '2026-10', 'ayer', ''):
            with self.subTest(value=value):
                with self.assertRaises(builder.ValidationError):
                    builder.day(value, 'fecha')

if __name__ == '__main__':
    unittest.main()
