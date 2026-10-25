#!/usr/bin/env python3
"""Autoridades HTTPS aceptadas por el catálogo de lectura."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_authority_qa', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class CatalogueAuthority(unittest.TestCase):
    def test_valid_https(self):
        for value in ('https://example.org/libro', 'https://example.org:443/libro', 'https://www.amazon.es/dp/1234567890'):
            with self.subTest(value=value):
                self.assertTrue(builder.https(value))

    def test_rejected_authorities(self):
        cases = [
            'http://example.org/libro',
            'https://usuario:clave@example.org/libro',
            'https://usuario@example.org/libro',
            'https://example.org:8443/libro',
            'https://example.org:invalido/libro',
            'https://example.org/linea\ninyectada',
            'https://example.org/<script>',
            '//example.org/libro',
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertFalse(builder.https(value))

if __name__ == '__main__':
    unittest.main()
