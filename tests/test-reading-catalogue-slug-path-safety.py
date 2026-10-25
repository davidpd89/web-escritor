#!/usr/bin/env python3
"""Seguridad de los slugs usados por el generador."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_slugs_qa', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class SlugPathSafety(unittest.TestCase):
    def test_valid_slugs(self):
        for value in ('libro', 'libro-2026', 'isbn-9788467083378', 'a1-b2'):
            with self.subTest(value=value):
                self.assertIsNotNone(builder.SLUG.fullmatch(value))

    def test_unsafe_slugs(self):
        for value in ('../libro', 'libro/otro', 'libro\\otro', 'Libro', 'libro--otro', '-libro', 'libro-', 'libro otro', 'libro%2Fotro', 'libro?x=1', 'libro#parte', ''):
            with self.subTest(value=value):
                self.assertIsNone(builder.SLUG.fullmatch(value))

if __name__ == '__main__':
    unittest.main()
