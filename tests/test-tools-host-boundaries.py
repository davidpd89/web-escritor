import json
import pathlib
import unittest
from urllib.parse import urlsplit, unquote

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ToolHostBoundaries(unittest.TestCase):
    def test_catalogue_destinations(self):
        data = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
        self.assertIsInstance(data, dict)
        tools = data.get('tools')
        self.assertIsInstance(tools, list)
        self.assertGreaterEqual(len(tools), 15)
        slugs = set()
        paths = set()
        for tool in tools:
            with self.subTest(tool=tool.get('slug')):
                slug = tool['slug']
                href = tool['href']
                self.assertNotIn(slug, slugs)
                slugs.add(slug)
                parsed = urlsplit(href)
                self.assertFalse(parsed.scheme or parsed.netloc)
                self.assertFalse(parsed.query or parsed.fragment)
                self.assertTrue(href.startswith('/'))
                self.assertFalse(href.startswith('//'))
                self.assertNotIn('\\', href)
                decoded = unquote(href)
                self.assertNotIn('..', decoded.split('/'))
                self.assertNotIn(href, paths)
                paths.add(href)
                target = ROOT / decoded.lstrip('/') / 'index.html'
                self.assertTrue(target.is_file(), str(target))

if __name__ == '__main__':
    unittest.main()