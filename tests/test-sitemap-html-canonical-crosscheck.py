import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class CanonicalParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        if tag != 'link':
            return
        data = dict(attrs)
        if 'canonical' in (data.get('rel') or '').lower().split():
            self.urls.append(data.get('href'))

class SitemapCanonical(unittest.TestCase):
    def test_canonical_matches_sitemap(self):
        tree = ET.parse(ROOT / 'sitemap.xml')
        checked = 0
        for entry in tree.findall('s:url', NS):
            url = entry.findtext('s:loc', namespaces=NS)
            if not url:
                continue
            path = unquote(urlsplit(url).path)
            file = ROOT / path.lstrip('/')
            if path.endswith('/'):
                file = file / 'index.html'
            if not file.is_file() or file.suffix != '.html':
                continue
            checked += 1
            parser = CanonicalParser()
            parser.feed(file.read_text(encoding='utf-8'))
            with self.subTest(file=str(file.relative_to(ROOT))):
                self.assertEqual(parser.urls, [url])
        self.assertGreater(checked, 0)

if __name__ == '__main__':
    unittest.main()