import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class RssIntegrity(unittest.TestCase):
    def test_items_have_unique_site_links(self):
        tree = ET.parse(ROOT / 'cuaderno/feed.xml')
        items = tree.findall('./channel/item')
        self.assertGreater(len(items), 0)
        links = []
        guids = []
        for item in items:
            link = item.findtext('link')
            guid = item.findtext('guid')
            self.assertTrue(link)
            self.assertTrue(guid)
            parsed = urlsplit(link)
            self.assertEqual(parsed.scheme, 'https')
            self.assertEqual(parsed.netloc, 'davidportodiaz.com')
            self.assertFalse(parsed.query or parsed.fragment)
            links.append(link)
            guids.append(guid)
        self.assertEqual(len(links), len(set(links)))
        self.assertEqual(len(guids), len(set(guids)))

if __name__ == '__main__':
    unittest.main()