#!/usr/bin/env python3
"""Contrato de títulos y descripciones SEO del catálogo publicado."""
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_title = False
        self.title_parts = []
        self.titles = []
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'head':
            self.in_head = True
        if not self.in_head:
            return
        if tag == 'title':
            self.in_title = True
            self.title_parts = []
        if tag == 'meta':
            key = a.get('name') or a.get('property')
            if key:
                self.meta.setdefault(key.lower(), []).append(a.get('content', ''))

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'title' and self.in_title:
            self.titles.append(''.join(self.title_parts).strip())
            self.in_title = False
        if tag == 'head':
            self.in_head = False

class GeneratedSeoMetadata(unittest.TestCase):
    def test_book_metadata(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        published = [b for b in catalogue['libros'] if b['estado'] == 'publicado']
        self.assertTrue(published, 'No hay libros publicados')
        titles = {}
        descriptions = {}
        for book in published:
            route = f'recomendaciones/libros/{book["slug"]}/index.html'
            with self.subTest(page=route):
                parser = HeadParser()
                parser.feed((ROOT / route).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.titles), 1, f'{route}: debe existir un único title')
                title = parser.titles[0]
                self.assertTrue(title, f'{route}: title vacío')
                self.assertIn(book['titulo'].casefold(), title.casefold(), f'{route}: title ajeno al libro')
                desc = parser.meta.get('description', [])
                self.assertEqual(len(desc), 1, f'{route}: description ausente o duplicada')
                self.assertTrue(desc[0].strip(), f'{route}: description vacía')
                for value, seen, field in [(title, titles, 'title'), (desc[0], descriptions, 'description')]:
                    key = ' '.join(value.casefold().split())
                    self.assertNotIn(key, seen, f'{route}: {field} duplicado con {seen.get(key)}')
                    seen[key] = route
                for key, expected in [('og:title', title), ('twitter:title', title), ('og:description', desc[0]), ('twitter:description', desc[0])]:
                    values = parser.meta.get(key, [])
                    if values:
                        self.assertEqual(values, [expected], f'{route}: {key} no coincide con HTML')

if __name__ == '__main__':
    unittest.main()