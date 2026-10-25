#!/usr/bin/env python3
"""Comprueba la exclusión de fichas no publicadas."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/reading-catalogue.json'


class PublicationExclusion(unittest.TestCase):
    def test_output_matches_publication_state(self):
        data = json.loads(DATA.read_text(encoding='utf-8'))
        books = data['libros']
        self.assertTrue(books)
        for book in books:
            with self.subTest(book=book['id'], state=book['estado']):
                page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
                if book['estado'] == 'publicado':
                    self.assertTrue(page.is_file(), 'Falta la ficha de una obra publicada')
                else:
                    self.assertFalse(page.exists(), 'Una obra no publicada conserva una ficha pública')


if __name__ == '__main__':
    unittest.main()
