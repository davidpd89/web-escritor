#!/usr/bin/env python3
"""Paridad entre catálogo publicado y entidades Book JSON-LD."""
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://davidportodiaz.com'

class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.capture = False
        self.parts = []
        self.canonicals = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and a.get('type', '').lower() == 'application/ld+json':
            self.capture = True
            self.parts = []
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonicals.append(a.get('href'))

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.blocks.append(json.loads(''.join(self.parts)))
            self.capture = False


def nodes(blocks):
    for block in blocks:
        for document in block if isinstance(block, list) else [block]:
            if not isinstance(document, dict):
                continue
            for node in document.get('@graph', [document]):
                if isinstance(node, dict):
                    yield node


def has_type(node, kind):
    value = node.get('@type', [])
    return kind in ([value] if isinstance(value, str) else value)

class BookIdentityParity(unittest.TestCase):
    def test_published_books(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = [b for b in catalogue['libros'] if b['estado'] == 'publicado']
        self.assertTrue(books, 'Catálogo: no hay libros publicados que comprobar')
        for book in books:
            slug = book['slug']
            route = f'recomendaciones/libros/{slug}/index.html'
            with self.subTest(page=route):
                parser = MetadataParser()
                parser.feed((ROOT / route).read_text(encoding='utf-8'))
                graph = list(nodes(parser.blocks))
                url = f'{SITE}/recomendaciones/libros/{slug}/'
                entities = [n for n in graph if has_type(n, 'Book') and n.get('url') == url]
                self.assertEqual(len(entities), 1, f'{route}: entidades Book principales: {len(entities)}')
                entity = entities[0]
                self.assertEqual(entity.get('name'), book['titulo'], f'{route}: título Book incorrecto')
                authors = entity.get('author', [])
                if isinstance(authors, dict):
                    authors = [authors]
                self.assertEqual([a.get('name') for a in authors], book['autores'], f'{route}: autores JSON-LD distintos')
                if book.get('isbn13'):
                    self.assertEqual(str(entity.get('isbn')), book['isbn13'], f'{route}: ISBN JSON-LD distinto')
                self.assertEqual(parser.canonicals, [url], f'{route}: canonical incorrecto')
                pages = [n for n in graph if has_type(n, 'WebPage') and n.get('url') == url]
                self.assertEqual(len(pages), 1, f'{route}: falta WebPage principal única')
                self.assertEqual(pages[0].get('mainEntity', {}).get('@id'), entity.get('@id'), f'{route}: mainEntity no identifica el libro')

if __name__ == '__main__':
    unittest.main()