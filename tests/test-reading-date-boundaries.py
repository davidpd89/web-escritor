#!/usr/bin/env python3
"""Fronteras de fechas usadas por el catálogo y el calendario ICS."""
from __future__ import annotations

import importlib.util
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('reading_dates_qa', ROOT / 'scripts/build-reading-catalogue.py')
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class DateBoundaries(unittest.TestCase):
    def test_valid_dates(self):
        cases = [
            '2024-02-29',
            '2000-02-29',
            '2026-02-28',
            '2026-04-30',
            '2026-12-31',
            '2027-01-01',
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertEqual(builder.day(value, 'fecha'), date.fromisoformat(value))

    def test_invalid_dates(self):
        cases = [
            '2026-02-29',
            '1900-02-29',
            '2026-04-31',
            '2026-13-01',
            '2026-00-10',
            '2026-01-00',
            '2026-01-32',
            '2026-1-01',
            '2026-01-1',
            '2026/01/01',
            '2026-01-01T00:00:00',
            '2026-01-01 ',
            '',
            None,
        ]
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(builder.ValidationError):
                    builder.day(value, 'fecha')


if __name__ == '__main__':
    unittest.main()
