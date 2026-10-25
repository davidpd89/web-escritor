import importlib.util
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_builder', ROOT / 'scripts/build-pagefind-index.py')
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)

class Titles(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        data = dict(attrs)
        if data.get('data-pagefind-meta') == 'title[content]':
            self.values.append(data.get('content'))

class RegistryTitleParity(unittest.TestCase):
    def test_real_registered_titles(self):
        registry = builder.load_registry_by_source(ROOT)
        pages = builder.eligible_pages(ROOT)
        checked = 0
        for rel in pages:
            entry = registry.get(rel, {})
            label = str(entry.get('label') or '').strip()
            if not label:
                continue
            original = (ROOT / rel).read_text(encoding='utf-8')
            generated = builder.inject_registry_search_title(original, entry)
            parser = Titles()
            parser.feed(generated)
            self.assertEqual(parser.values, [label], f'{rel}: título Pagefind distinto de {label!r}; obtenido {parser.values!r}')
            checked += 1
        self.assertGreater(checked, 0, 'No se encontraron páginas reales con títulos registrados')

if __name__ == '__main__':
    unittest.main()
