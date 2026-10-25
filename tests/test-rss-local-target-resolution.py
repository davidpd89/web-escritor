import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class RssTargets(unittest.TestCase):
    def test_every_item_resolves_locally(self):
        items = ET.parse(ROOT / 'cuaderno/feed.xml').findall('./channel/item')
        self.assertTrue(items)
        for item in items:
            url = item.findtext('link')
            with self.subTest(url=url):
                parsed = urlsplit(url)
                self.assertEqual(parsed.netloc, 'davidportodiaz.com')
                path = unquote(parsed.path)
                target = ROOT / path.lstrip('/')
                if path.endswith('/'):
                    target = target / 'index.html'
                self.assertTrue(target.is_file(), str(target))
                self.assertEqual(target.suffix, '.html')

if __name__ == '__main__':
    unittest.main()