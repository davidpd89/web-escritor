import importlib.util
import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('atlas', ROOT / 'scripts/build-atlas-literario.py')
atlas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atlas)

class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attributes = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'article' and 'data-atlas-card' in values:
            self.attributes.append(values)

class AttributeInjection(unittest.TestCase):
    def test_category_is_never_interpreted_as_html(self):
        original = json.loads((ROOT / 'data/atlas-literario.json').read_text(encoding='utf-8'))
        attacks = ['bibliotecas" onmouseover="alert(1)', 'x" autofocus="autofocus', '<img src=x onerror=alert(1)>']
        for payload in attacks:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                data = dict(original)
                data['categories'] = [{'slug': payload, 'name': 'Categoría de prueba'}]
                item = dict(original['items'][0])
                item.update(status='published', category=payload, verified_date='2026-08-20', image={'src': '/assets/test.webp', 'alt': 'Prueba', 'credit': 'QA', 'license': 'CC0', 'source_url': 'https://example.org/image'})
                data['items'] = [item]
                source = Path(directory) / 'source.json'
                source.write_text(json.dumps(data), encoding='utf-8')
                try:
                    loaded, categories = atlas.load(source)
                except ValueError:
                    continue
                output = Path(directory) / 'output'
                atlas.build(loaded, categories, output)
                parser = Cards()
                parser.feed((output / 'index.html').read_text(encoding='utf-8'))
                self.assertEqual(len(parser.attributes), 1)
                attributes = parser.attributes[0]
                self.assertEqual(attributes.get('data-category'), payload)
                self.assertFalse(any(name.startswith('on') or name in ('autofocus', 'style') for name in attributes))

if __name__ == '__main__':
    unittest.main()