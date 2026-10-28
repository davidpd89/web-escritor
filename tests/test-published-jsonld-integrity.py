import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type', '').lower() == 'application/ld+json':
            self.active = True
            self.blocks.append('')
    def handle_data(self, data):
        if self.active:
            self.blocks[-1] += data
    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

def nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from nodes(item)
    elif isinstance(value, dict):
        yield value
        if '@graph' in value:
            yield from nodes(value['@graph'])

class TestJsonLd(unittest.TestCase):
    def test_jsonld_on_published_pages(self):
        tree = ET.parse(ROOT / 'sitemap.xml')
        urls = [e.text for e in tree.findall('.//s:loc', NS)]
        checked = 0
        for url in urls:
            path = urlsplit(url).path
            file = ROOT / (path.lstrip('/') + 'index.html' if path.endswith('/') else path.lstrip('/'))
            if not file.is_file():
                continue
            parser = Scripts()
            parser.feed(file.read_text(encoding='utf-8'))
            for number, block in enumerate(parser.blocks, 1):
                with self.subTest(url=url, block=number):
                    value = json.loads(block)
                    self.assertIsInstance(value, (dict, list), f'{url}: JSON-LD raíz inválida')
                    objects = list(nodes(value))
                    self.assertTrue(objects, f'{url}: JSON-LD vacío')
                    contexts = [x.get('@context') for x in objects if '@context' in x]
                    self.assertTrue(any(isinstance(c, str) and c.rstrip('/') in ('https://schema.org', 'http://schema.org') for c in contexts), f'{url}: bloque {number} sin contexto Schema.org')
                    checked += 1
        self.assertGreater(checked, 0, 'Ningún JSON-LD publicado fue analizado')

if __name__ == '__main__':
    unittest.main()