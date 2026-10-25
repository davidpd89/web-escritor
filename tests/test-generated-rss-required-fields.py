import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rss_fields', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RssRequiredFields(unittest.TestCase):
    def test_incomplete_items_are_not_emitted(self):
        records = [
            {'title': 'Válido', 'url': 'https://davidportodiaz.com/cuaderno/valido/', 'date': '2026-10-01'},
            {'title': 'Sin enlace', 'url': None},
            {'title': None, 'url': 'https://davidportodiaz.com/cuaderno/sin-titulo/'},
            {'title': ' ', 'url': 'https://davidportodiaz.com/cuaderno/blanco/'},
            {'title': 'Sin URL real', 'url': ' '},
        ]
        xml = ET.fromstring(mod.build_feed_bytes(records))
        items = xml.findall('./channel/item')
        self.assertEqual(len(items), 1)
        for item in items:
            title = item.findtext('title')
            link = item.findtext('link')
            guid = item.findtext('guid')
            self.assertTrue(title and title.strip())
            self.assertTrue(link and link.strip())
            self.assertEqual(guid, link)

if __name__ == '__main__':
    unittest.main()
