#!/usr/bin/env python3
"""Detecta acciones repetidas en fichas generadas."""
from __future__ import annotations

import json
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href', ''))


class ActionUniqueness(unittest.TestCase):
    def test_published_book_actions_are_not_duplicated(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.assertTrue(books)
        for book in books:
            with self.subTest(book=book['id']):
                page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
                parser = Anchors()
                parser.feed(page.read_text(encoding='utf-8'))
                calendar = [h for h in parser.links if h == '/recomendaciones/proximos-lanzamientos.ics']
                self.assertLessEqual(len(calendar), 1)
                expected_purchase_urls = {
                    option['url'] for option in book.get('formatos_compra', [])
                }
                for destination in expected_purchase_urls:
                    self.assertIn(destination, parser.links, 'Falta un destino comercial declarado')
                commerce = [h for h in parser.links if urlparse(h).hostname in {'amazon.es', 'www.amazon.es', 'amzn.to'}]
                duplicates = {url: count for url, count in Counter(commerce).items() if count > 1}
                self.assertFalse(duplicates, f'Enlaces comerciales duplicados: {duplicates}')


if __name__ == '__main__':
    unittest.main()
