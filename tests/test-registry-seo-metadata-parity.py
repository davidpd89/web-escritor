import json
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.titles = []
        self.descriptions = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title':
            self.in_title = True
            self.titles.append('')
        if tag == 'meta' and a.get('name', '').lower() == 'description':
            self.descriptions.append(a.get('content', '').strip())
    def handle_data(self, data):
        if self.in_title:
            self.titles[-1] += data
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

class TestRegistryMetadata(unittest.TestCase):
    def test_public_pages_have_seo_metadata(self):
        registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
        defaults = registry.get('defaults', {})
        checked = 0
        for entry in registry['entries']:
            item = {**defaults, **entry}
            if item.get('status') != 'public' or not item.get('sitemap', True):
                continue
            source = item.get('sourceFile', '')
            if not source.endswith('.html'):
                continue
            file = ROOT / source
            with self.subTest(source=source):
                self.assertTrue(file.is_file(), f'{source}: falta HTML registrado')
                parser = Metadata()
                parser.feed(file.read_text(encoding='utf-8'))
                self.assertEqual(len(parser.titles), 1, f'{source}: title ausente o duplicado')
                self.assertTrue(parser.titles[0].strip(), f'{source}: title vacío')
                self.assertEqual(len(parser.descriptions), 1, f'{source}: meta description ausente o duplicada')
                self.assertTrue(parser.descriptions[0], f'{source}: meta description vacía')
                checked += 1
        self.assertGreater(checked, 0, 'No se comprobaron páginas públicas del registro')

if __name__ == '__main__':
    unittest.main()