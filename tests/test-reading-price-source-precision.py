#!/usr/bin/env python3
"""Precisión monetaria de los PVP del catálogo real."""
import json
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))


class PricePrecision(unittest.TestCase):
    def test_published_prices_preserve_exact_cents(self):
        books = [b for b in DATA['libros'] if b['estado'] == 'publicado' and b.get('pvp_centimos') is not None]
        for book in books:
            with self.subTest(book=book['slug']):
                cents = book['pvp_centimos']
                self.assertIs(type(cents), int, f'{book["slug"]}: PVP no entero')
                self.assertGreaterEqual(cents, 100, f'{book["slug"]}: PVP inferior al mínimo bibliográfico')
                euros = Decimal(cents) / Decimal(100)
                serialized = format(euros, '.2f')
                self.assertEqual(int(Decimal(serialized) * 100), cents, f'{book["slug"]}: pérdida de céntimos al serializar {cents}')
                self.assertRegex(book.get('pvp_fecha_verificacion', ''), r'^\d{4}-\d{2}-\d{2}$', f'{book["slug"]}: PVP sin fecha de verificación')


if __name__ == '__main__':
    unittest.main()
