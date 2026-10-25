#!/usr/bin/env python3
"""Paridad de categorías entre datos y fichas publicadas. Sin red."""
from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/reading-catalogue.json'


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.append(dict(attrs).get('href', ''))


class CategoryParity(unittest.TestCase):
    def test_all_published_book_categories_have_exact_links(self):
        data = json.loads(DATA.read_text(encoding='utf-8'))
        categories = {c['id']: c for c in data['categorias'] if c['activa']}
        published = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.assertTrue(published)
        for book in published:
            with self.subTest(book=book['id']):
                expected = {
                    '/recomendaciones/#' + categories[r['categoria_id']]['tipo'] + '=' + r['categoria_id']
                    for r in data['libro_categorias']
                    if r['libro_id'] == book['id'] and r['categoria_id'] in categories
                }
                page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
                parser = Links()
                parser.feed(page.read_text(encoding='utf-8'))
                actual = [unquote(h) for h in parser.hrefs if h.startswith('/recomendaciones/#')]
                self.assertEqual(set(actual), expected)
                self.assertEqual(len(actual), len(set(actual)), 'Enlaces de filtro duplicados')


if __name__ == '__main__':
    unittest.main()
