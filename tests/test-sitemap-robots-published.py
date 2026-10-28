import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class RobotsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.directives = []
    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        if a.get('name', '').lower() in ('robots', 'googlebot'):
            self.directives.extend(x.strip().lower() for x in a.get('content', '').split(','))

class TestPublishedRobots(unittest.TestCase):
    def test_sitemap_does_not_announce_noindex(self):
        tree = ET.parse(ROOT / 'sitemap.xml')
        urls = [e.text for e in tree.findall('.//s:loc', NS)]
        self.assertTrue(urls, 'sitemap.xml: sin URLs')
        for url in urls:
            with self.subTest(url=url):
                path = urlsplit(url).path
                file = ROOT / (path.lstrip('/') + 'index.html' if path.endswith('/') else path.lstrip('/'))
                self.assertTrue(file.is_file(), f'{url}: falta HTML')
                parser = RobotsParser()
                parser.feed(file.read_text(encoding='utf-8'))
                self.assertNotIn('noindex', parser.directives, f'{url}: noindex contradice sitemap.xml')
                self.assertNotIn('none', parser.directives, f'{url}: robots none contradice sitemap.xml')

if __name__ == '__main__':
    unittest.main()