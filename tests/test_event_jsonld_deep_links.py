import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.blocks = []
        self.capture = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'a' and a.get('name'):
            self.ids.add(a['name'])
        if tag == 'script' and a.get('type', '').lower() == 'application/ld+json':
            self.capture = True
            self.parts = []

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.blocks.append(''.join(self.parts))
            self.capture = False

    def events(self):
        result = []
        def visit(value):
            if isinstance(value, list):
                for item in value:
                    visit(item)
            elif isinstance(value, dict):
                types = value.get('@type', [])
                if types == 'Event' or isinstance(types, list) and 'Event' in types:
                    result.append(value)
                for item in value.values():
                    visit(item)
        for block in self.blocks:
            visit(json.loads(block))
        return result

class DeepLinks(unittest.TestCase):
    def test_published_event_destinations(self):
        for page in ('eventos.html', 'ferias.html'):
            with self.subTest(page=page):
                document = Document()
                document.feed((ROOT / page).read_text(encoding='utf-8'))
                events = document.events()
                self.assertTrue(events, f'{page}: no se encontraron eventos JSON-LD')
                seen = set()
                for event in events:
                    identity = event.get('@id', '')
                    url = event.get('url', identity)
                    self.assertTrue(identity, f'{page}: Event sin @id')
                    self.assertNotIn(identity, seen, f'{page}: @id duplicado {identity}')
                    seen.add(identity)
                    for field, value in (('@id', identity), ('url', url)):
                        parsed = urlsplit(value)
                        self.assertEqual(parsed.scheme, 'https', f'{page}: {field} no usa HTTPS: {value}')
                        self.assertEqual(parsed.hostname, 'davidportodiaz.com', f'{page}: {field} apunta a otro dominio: {value}')
                        self.assertEqual(parsed.path, '/' + page, f'{page}: {field} apunta a otra página: {value}')
                        self.assertIn(unquote(parsed.fragment), document.ids,
                            f'{page}: {field} tiene un fragmento inexistente: {value}')

if __name__ == '__main__':
    unittest.main()
