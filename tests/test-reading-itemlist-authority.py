import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'recomendaciones/index.html'

class JSONScripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.documents = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = dict(attrs).get('type') == 'application/ld+json'
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.documents.append(json.loads(''.join(self.parts)))
            self.active = False

def walk(value):
    if isinstance(value, list):
        for item in value:
            yield from walk(item)
    elif isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)

class TestReadingAuthority(unittest.TestCase):
    def test_itemlist_targets(self):
        parser = JSONScripts()
        parser.feed(PAGE.read_text(encoding='utf-8'))
        lists = [node for document in parser.documents for node in walk(document) if node.get('@type') == 'ItemList' and node.get('itemListElement')]
        self.assertTrue(lists, f'{PAGE}: falta ItemList con elementos')
        checked = set()
        for listing in lists:
            elements = listing['itemListElement']
            positions = []
            for entry in elements:
                item = entry.get('item', {})
                url = item.get('url') or item.get('@id')
                self.assertIsInstance(url, str, f'{PAGE}: ListItem sin URL: {entry}')
                parsed = urlsplit(url)
                with self.subTest(url=url):
                    self.assertEqual((parsed.scheme, parsed.hostname), ('https', 'davidportodiaz.com'), f'{PAGE}: autoridad incorrecta: {url}')
                    self.assertFalse(parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment, f'{PAGE}: URL bibliográfica no canónica: {url}')
                    path = unquote(parsed.path)
                    self.assertTrue(path.startswith('/recomendaciones/libros/') and path.endswith('/'), f'{PAGE}: destino fuera del catálogo: {url}')
                    self.assertNotIn('..', Path(path).parts, f'{PAGE}: traversal en {url}')
                    target = ROOT / path.lstrip('/') / 'index.html'
                    self.assertTrue(target.is_file(), f'{PAGE}: ficha anunciada inexistente: {url}')
                    self.assertNotIn(url, checked, f'{PAGE}: ficha repetida en ItemList: {url}')
                    checked.add(url)
                positions.append(entry.get('position'))
            self.assertEqual(positions, list(range(1, len(elements) + 1)), f'{PAGE}: posiciones ItemList incorrectas: {positions}')

if __name__ == '__main__':
    unittest.main()