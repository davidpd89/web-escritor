import pathlib
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]

class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.robots = []
        self.refresh = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonicals.append(attrs.get('href'))
        if tag == 'meta' and attrs.get('name', '').lower() == 'robots':
            self.robots.append(attrs.get('content', ''))
        if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'refresh':
            self.refresh.append(attrs.get('content', ''))

class RSSCanonical(unittest.TestCase):
    def test_rss_canonical(self):
        items = ET.parse(ROOT / 'cuaderno/feed.xml').findall('./channel/item')
        self.assertTrue(items)
        for item in items:
            url = item.findtext('link')
            with self.subTest(url=url):
                path = ROOT / urlsplit(url).path.lstrip('/') / 'index.html'
                self.assertTrue(path.is_file())
                parser = HeadParser()
                parser.feed(path.read_text(encoding='utf-8'))
                self.assertEqual(parser.canonicals, [url])
                self.assertFalse(parser.refresh)
                self.assertTrue(parser.robots)
                directives = ','.join(parser.robots).lower()
                self.assertFalse(re.search(r'\b(noindex|none)\b', directives))
                self.assertRegex(directives, r'\bindex\b')

if __name__ == '__main__':
    unittest.main()