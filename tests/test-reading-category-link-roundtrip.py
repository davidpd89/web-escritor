#!/usr/bin/env python3
"""Paridad entre relaciones del catálogo y enlaces HTML de categorías."""
from __future__ import annotations

import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('reading_category_qa', ROOT / 'scripts/build-reading-catalogue.py')
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = {'href': dict(attrs).get('href', ''), 'text': ''}

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.current['text'] = ' '.join(self.current['text'].split())
            self.links.append(self.current)
            self.current = None


class CategoryLinkParity(unittest.TestCase):
    def test_all_active_relations_roundtrip(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = builder.validate(data, ROOT)
        self.assertTrue(books)
        for book in books:
            with self.subTest(book=book['id']):
                active = builder.categories(data, book)
                expected = {(c['tipo'], c['id']): c['nombre'] for c in active}
                self.assertEqual(len(expected), len(active))
                parser = Links()
                parser.feed(builder.tags(active))
                actual = {}
                for link in parser.links:
                    url = urlsplit(link['href'])
                    self.assertEqual(url.path, '/recomendaciones/')
                    self.assertFalse(url.query)
                    params = parse_qs(url.fragment, keep_blank_values=True)
                    self.assertEqual(len(params), 1)
                    kind, values = next(iter(params.items()))
                    self.assertEqual(len(values), 1)
                    key = (kind, values[0])
                    self.assertNotIn(key, actual, f'Enlace de categoría duplicado: {key}')
                    actual[key] = link['text']
                self.assertEqual(actual, expected)
                compact = Links()
                compact.feed(builder.tags(active, compact=True))
                self.assertEqual(len(compact.links), min(3, len(active)))


if __name__ == '__main__':
    unittest.main()
