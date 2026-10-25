import pathlib
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]

class EditorialRSSIntegrity(unittest.TestCase):
    def test_feed_targets(self):
        root = ET.parse(ROOT / 'cuaderno/feed.xml').getroot()
        self.assertEqual(root.tag, 'rss')
        items = root.findall('./channel/item')
        self.assertGreater(len(items), 0)
        guids = set()
        for item in items:
            with self.subTest(item=item.findtext('title')):
                title = (item.findtext('title') or '').strip()
                description = (item.findtext('description') or '').strip()
                link = (item.findtext('link') or '').strip()
                guid = (item.findtext('guid') or '').strip()
                self.assertTrue(title)
                self.assertTrue(description)
                self.assertEqual(guid, link)
                self.assertNotIn(guid, guids)
                guids.add(guid)
                parsed = urllib.parse.urlsplit(link)
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(parsed.netloc, 'davidportodiaz.com')
                self.assertTrue(parsed.path.startswith('/cuaderno/'))
                self.assertFalse(parsed.query or parsed.fragment)
                self.assertTrue((ROOT / parsed.path.lstrip('/') / 'index.html').is_file())
                datetime.strptime(item.findtext('pubDate'), '%a, %d %b %Y %H:%M:%S %z')

if __name__ == '__main__':
    unittest.main()