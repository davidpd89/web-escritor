#!/usr/bin/env python3
"""Precisión de fechas bibliográficas sin fechas sintéticas."""
import importlib.util
import json
import re
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_date_precision', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
DATA = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))


class PublicationPrecision(unittest.TestCase):
    def test_real_books_keep_source_precision(self):
        books = [b for b in DATA['libros'] if b['estado'] == 'publicado']
        self.assertTrue(books, 'No se encontraron libros publicados')
        for book in books:
            with self.subTest(book=book['slug']):
                label = builder.publication_date_label(book)
                exact = book.get('fecha_publicacion')
                partial = book.get('fecha_publicacion_parcial')
                year = book.get('anio_publicacion')
                if exact:
                    d = date.fromisoformat(exact)
                    expected = f'{d.day} de {builder.MONTHS_ES[d.month]} de {d.year}'
                elif partial:
                    y, m = map(int, partial.split('-'))
                    expected = f'{builder.MONTHS_ES[m]} de {y}'
                else:
                    expected = str(year or '')
                self.assertEqual(label, expected, f'{book["slug"]}: fecha visible {label!r}; fuente {exact or partial or year!r}')
                if partial and not exact:
                    self.assertFalse(re.match(r'^\d{1,2} de ', label), f'{book["slug"]}: se inventó un día para {partial}')


if __name__ == '__main__':
    unittest.main()
