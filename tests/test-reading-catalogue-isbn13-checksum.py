#!/usr/bin/env python3
"""Comprobación bibliográfica ISBN-13."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_isbn_qa', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class ISBN13Checksum(unittest.TestCase):
    def test_known_valid_isbn(self):
        self.assertTrue(builder.valid_isbn('9788467083378'))

    def test_mutated_check_digit(self):
        source = '9788467083378'
        for digit in '0123456789':
            candidate = source[:-1] + digit
            with self.subTest(candidate=candidate):
                self.assertEqual(builder.valid_isbn(candidate), candidate == source)

    def test_invalid_format(self):
        for value in ('978846708337', '97884670833780', '978-84-670-8337-8', '1238467083378', '', None):
            with self.subTest(value=value):
                self.assertFalse(builder.valid_isbn(value))

if __name__ == '__main__':
    unittest.main()
