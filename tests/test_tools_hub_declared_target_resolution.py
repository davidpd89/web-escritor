import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))

class ToolTargetResolution(unittest.TestCase):
    def test_every_tool_has_document_and_source(self):
        self.assertGreaterEqual(len(DATA['tools']), 5)
        for item in DATA['tools']:
            with self.subTest(tool=item['slug']):
                href = item['href']
                parsed = urlsplit(href)
                self.assertEqual(parsed.scheme, '')
                self.assertEqual(parsed.netloc, '')
                self.assertFalse(parsed.query or parsed.fragment)
                self.assertTrue(href.startswith('/herramientas/'))
                self.assertNotIn('..', Path(href).parts)
                destination = ROOT / href.lstrip('/') / 'index.html'
                self.assertTrue(destination.is_file(), 'Página inexistente: ' + href)
                source = ROOT / item['source_doc']
                self.assertTrue(source.is_file(), 'Código inexistente: ' + item['source_doc'])

    def test_directories_are_navigable(self):
        for item in DATA.get('directories', []):
            with self.subTest(directory=item['href']):
                href = item['href']
                self.assertTrue(href.startswith('/') and not href.startswith('//'))
                relative = href.lstrip('/')
                target = ROOT / relative
                self.assertTrue((target / 'index.html').is_file() if href.endswith('/') else target.is_file(), 'Directorio sin destino: ' + href)

if __name__ == '__main__':
    unittest.main()