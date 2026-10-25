#!/usr/bin/env python3
"""Accesibilidad básica de todas las fichas de lectura publicadas."""
from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Structure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1_count = 0
        self.images = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'h1':
            self.h1_count += 1
        if tag == 'img':
            self.images.append(attributes)


class BookAccessibility(unittest.TestCase):
    def test_published_book_semantic_structure(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.assertTrue(books)
        for book in books:
            with self.subTest(book=book['id']):
                page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
                parser = Structure()
                parser.feed(page.read_text(encoding='utf-8'))
                self.assertEqual(parser.h1_count, 1)
                cover = book['portada_local']
                matches = [image for image in parser.images if urlsplit(image.get('src', '')).path == cover]
                self.assertTrue(matches, 'Portada declarada ausente del HTML')
                for image in matches:
                    self.assertTrue(image.get('alt', '').strip(), 'Portada sin alternativa textual')


if __name__ == '__main__':
    unittest.main()
