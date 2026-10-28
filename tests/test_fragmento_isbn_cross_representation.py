import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ['fragmento/index.html', 'libros/samuel-entre-mundos/index.html', 'libros/index.html']

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.json_blocks = []
        self.in_json = False
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('property') == 'books:isbn':
            self.meta['isbn'] = a.get('content')
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.in_json = True
            self.buffer = []

    def handle_data(self, data):
        if self.in_json:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.in_json:
            self.json_blocks.append(json.loads(''.join(self.buffer)))
            self.in_json = False

def walk(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)

class ISBNParity(unittest.TestCase):
    def test_published_samuel_identity(self):
        documents = {}
        for route in ROUTES:
            source = (ROOT / route).read_text(encoding='utf-8')
            doc = Document()
            doc.feed(source)
            documents[route] = (source, doc)

        reference = documents[ROUTES[0]][1].meta.get('isbn')
        self.assertRegex(reference or '', r'^\d{13}$', f'{ROUTES[0]}: books:isbn ausente o inválido')
        self.assertEqual(sum((1 if i % 2 == 0 else 3) * int(c) for i, c in enumerate(reference[:12])) % 10, (10 - int(reference[-1])) % 10, f'{ROUTES[0]}: ISBN sin dígito de control válido')

        for route, (source, doc) in documents.items():
            with self.subTest(route=route):
                self.assertIn(reference, source, f'{route}: falta ISBN {reference}')
                declared = [str(node['isbn']) for block in doc.json_blocks for node in walk(block) if 'isbn' in node and ('Samuel entre mundos' in str(node.get('name', '')) or route != 'libros/index.html')]
                if route != ROUTES[0]:
                    self.assertTrue(declared, f'{route}: no se encontró ISBN bibliográfico JSON-LD de Samuel')
                for isbn in declared:
                    self.assertEqual(isbn, reference, f'{route}: JSON-LD publica ISBN {isbn}, esperado {reference}')
                if 'books:isbn' in source:
                    self.assertEqual(doc.meta.get('isbn'), reference, f'{route}: books:isbn distinto de {reference}')

if __name__ == '__main__':
    unittest.main()