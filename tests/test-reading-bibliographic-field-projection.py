#!/usr/bin/env python3
"""Proyección bibliográfica real del catálogo publicado."""
import html
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading = []
        self.in_h1 = False
        self.in_json = False
        self.json_parts = []
        self.blocks = []
        self.terms = []
        self.values = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.in_h1 = True
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_json = True
            self.json_parts = []
        if tag in ('dt', 'dd'):
            self.current = [tag, []]

    def handle_data(self, data):
        if self.in_h1:
            self.heading.append(data)
        if self.in_json:
            self.json_parts.append(data)
        if self.current:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.in_h1 = False
        if tag == 'script' and self.in_json:
            self.blocks.append(json.loads(''.join(self.json_parts)))
            self.in_json = False
        if self.current and tag == self.current[0]:
            value = ' '.join(''.join(self.current[1]).split())
            (self.terms if tag == 'dt' else self.values).append(value)
            self.current = None


def nodes(obj):
    if isinstance(obj, list):
        for value in obj:
            yield from nodes(value)
    elif isinstance(obj, dict):
        yield obj
        if '@graph' in obj:
            yield from nodes(obj['@graph'])


def published_pages():
    for book in DATA['libros']:
        if book['estado'] != 'publicado':
            continue
        path = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
        parser = PageParser()
        parser.feed(path.read_text(encoding='utf-8'))
        books = [n for block in parser.blocks for n in nodes(block) if 'Book' in ([n.get('@type')] if isinstance(n.get('@type'), str) else n.get('@type', []))]
        yield book, path, parser, books


class BibliographicProjection(unittest.TestCase):
    def test_titles_match_heading_and_schema(self):
        for book, path, page, schemas in published_pages():
            with self.subTest(page=str(path)):
                self.assertEqual(' '.join(''.join(page.heading).split()), book['titulo'], f'{path}: H1 distinto del título {book["titulo"]!r}')
                self.assertEqual(len(schemas), 1, f'{path}: se esperaba un Book JSON-LD')
                self.assertEqual(schemas[0]['name'], book['titulo'], f'{path}: Book.name incorrecto')

    def test_isbn_matches_visible_edition_and_schema(self):
        for book, path, page, schemas in published_pages():
            if not book.get('isbn13'):
                continue
            with self.subTest(page=str(path)):
                self.assertEqual(len(schemas), 1, f'{path}: falta Book JSON-LD')
                self.assertEqual(schemas[0].get('isbn'), book['isbn13'], f'{path}: ISBN estructurado distinto de {book["isbn13"]}')
                fields = dict(zip(page.terms, page.values))
                self.assertEqual(fields.get('ISBN-13'), book['isbn13'], f'{path}: ISBN visible distinto de {book["isbn13"]}')

    def test_page_counts_match_schema(self):
        for book, path, page, schemas in published_pages():
            if not book.get('numero_paginas'):
                continue
            with self.subTest(page=str(path)):
                self.assertEqual(len(schemas), 1, f'{path}: falta Book JSON-LD')
                self.assertEqual(schemas[0].get('numberOfPages'), book['numero_paginas'], f'{path}: número de páginas incorrecto; esperado {book["numero_paginas"]}')


if __name__ == '__main__':
    unittest.main()
