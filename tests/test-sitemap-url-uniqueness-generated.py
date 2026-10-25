import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class SitemapUrls(unittest.TestCase):
    def test_unique_canonical_urls(self):
        root = ET.parse(ROOT / 'sitemap.xml').getroot()
        urls = [entry.findtext('s:loc', namespaces=NS) for entry in root.findall('s:url', NS)]
        self.assertTrue(urls)
        self.assertEqual(len(urls), len(set(urls)))
        for url in urls:
            with self.subTest(url=url):
                parsed = urlsplit(url)
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(parsed.netloc, 'davidportodiaz.com')
                self.assertFalse(parsed.query)
                self.assertFalse(parsed.fragment)
                self.assertTrue(parsed.path.startswith('/'))
                self.assertNotIn('//', parsed.path)

if __name__ == '__main__':
    unittest.main()