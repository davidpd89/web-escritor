import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))

class ToolTraceability(unittest.TestCase):
    def test_registry_has_unique_identities(self):
        tools = DATA['tools']
        self.assertTrue(tools)
        for key in ('slug', 'href'):
            values = [tool[key] for tool in tools]
            self.assertEqual(len(values), len(set(values)), f'Duplicados en {key}')

    def test_local_tools_have_real_implementations(self):
        local = [tool for tool in DATA['tools'] if tool.get('privacy') == 'local']
        self.assertTrue(local)
        for tool in local:
            with self.subTest(slug=tool['slug']):
                href = tool['href']
                parsed = urlsplit(href)
                self.assertFalse(parsed.scheme or parsed.netloc or parsed.query or parsed.fragment)
                self.assertTrue(href.startswith('/herramientas/'))
                self.assertTrue(href.endswith('/'))
                target = (ROOT / href.lstrip('/') / 'index.html').resolve()
                self.assertTrue(target.is_relative_to(ROOT.resolve()))
                self.assertTrue(target.is_file(), str(target))
                source = tool.get('source_doc')
                self.assertIsInstance(source, str)
                self.assertTrue(source)
                source_path = (ROOT / source).resolve()
                self.assertTrue(source_path.is_relative_to(ROOT.resolve()))
                self.assertTrue(source_path.is_file(), str(source_path))
                self.assertIn(source_path.suffix, {'.js', '.mjs'})

    def test_local_claim_does_not_use_external_destination(self):
        for tool in DATA['tools']:
            with self.subTest(slug=tool['slug']):
                href = tool['href']
                self.assertNotIn('\\', href)
                self.assertNotIn('..', href.split('/'))
                self.assertNotIn('//', href)

if __name__ == '__main__':
    unittest.main()
