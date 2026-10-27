import importlib.util
import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_builder', ROOT / 'scripts/build-pagefind-index.py')
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)

class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)

def titles(source):
    parser = Extract()
    parser.feed(source)
    return ''.join(parser.title).strip()

def structured_names(source):
    names = []
    for raw in re.findall(r'<script\b[^>]*type=[\'\"]application/ld\+json[\'\"][^>]*>(.*?)</script\s*>', source, re.I | re.S):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if isinstance(node, dict) and isinstance(node.get('name'), str):
                names.append(node['name'])
    return names

class TitlePreservation(unittest.TestCase):
    def test_index_preparation_preserves_publication_titles(self):
        registry = builder.load_registry_by_source(ROOT)
        checked = 0
        for rel in builder.eligible_pages(ROOT):
            original = (ROOT / rel).read_text(encoding='utf-8')
            generated = builder.inject_registry_search_title(original, registry.get(rel))
            self.assertEqual(titles(generated), titles(original), f'{rel}: se modificó el título HTML publicado')
            self.assertEqual(structured_names(generated), structured_names(original), f'{rel}: cambiaron los nombres JSON-LD publicados')
            checked += 1
        self.assertGreater(checked, 0, 'No hay documentos indexables que comprobar')

if __name__ == '__main__':
    unittest.main()
