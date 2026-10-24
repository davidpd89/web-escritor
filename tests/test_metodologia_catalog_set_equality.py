import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CatalogSetEquality(unittest.TestCase):
    def test_methodology_directory_and_details(self):
        data = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
        expected = {p['slug'] for p in data['publishers'] if p.get('publish') is True}
        index = (ROOT / 'editoriales/index.html').read_text(encoding='utf-8')
        method = (ROOT / 'metodologia-editorial/index.html').read_text(encoding='utf-8')
        card_slugs = re.findall(r'<h2><a href="/editoriales/([^/]+)/">', index)
        directories = {p.parent.name for p in (ROOT / 'editoriales').glob('*/index.html')}
        self.assertEqual(len(card_slugs), len(set(card_slugs)), 'Tarjetas duplicadas')
        self.assertEqual(set(card_slugs), expected, 'Diferencia entre tarjetas y datos')
        self.assertEqual(directories, expected, 'Fichas inexistentes o sobrantes')
        word = 'ficha' if len(expected) == 1 else 'fichas'
        self.assertIn('Actualmente el directorio publica {} {}.'.format(len(expected), word), method)

if __name__ == '__main__':
    unittest.main()