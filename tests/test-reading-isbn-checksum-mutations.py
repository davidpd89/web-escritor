#!/usr/bin/env python3
"""Pruebas deterministas de integridad ISBN-13."""
from __future__ import annotations

import importlib.util
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('reading_isbn_qa', ROOT / 'scripts/build-reading-catalogue.py')
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def make_isbn(prefix):
    total = sum(int(n) * (1 if i % 2 == 0 else 3) for i, n in enumerate(prefix))
    return prefix + str((-total) % 10)


class ISBNMutations(unittest.TestCase):
    def test_valid_and_corrupted_check_digits(self):
        rng = random.Random(20261025)
        for family in ('978', '979'):
            for _ in range(100):
                prefix = family + ''.join(str(rng.randrange(10)) for _ in range(9))
                isbn = make_isbn(prefix)
                self.assertTrue(builder.valid_isbn(isbn), isbn)
                for digit in '0123456789':
                    if digit != isbn[-1]:
                        self.assertFalse(builder.valid_isbn(isbn[:-1] + digit))

    def test_invalid_format_and_unicode_digits(self):
        valid = make_isbn('978123456789')
        cases = [
            valid[:-1],
            valid + '0',
            '977' + valid[3:],
            valid[:3] + '-' + valid[3:],
            ' ' + valid,
            valid + '\n',
            valid[:5] + 'A' + valid[6:],
            valid.replace('1', '\u0661', 1),
            None,
            9781234567890,
            '',
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertFalse(builder.valid_isbn(value))


if __name__ == '__main__':
    unittest.main()
