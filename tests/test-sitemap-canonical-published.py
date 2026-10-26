import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://davidportodiaz.com'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
    def handle_starttag(self, tag, attrs):
        if tag != 'link':
            return
        a = dict(attrs)
        if 'canonical' in a.get('rel', '').lower().split():
            self.canonicals.append(a.get('href', ''))

def normalize(url):
    p = urlsplit(url)
    path = p.path.rstrip('/') or '/'
    return p.scheme.lower(), p.netloc.lower(), path

class TestSitemapCanonical(unittest.TestCase):
    def test_published_canonicals(self):
        tree = ET.parse(ROOT / 'sitemap.xml')
        urls = [x.text for x in tree.findall('.//s:loc', NS)]
        self.assertTrue(urls, 'sitemap.xml: no contiene URLs')
        for url in urls:
            with self.subTest(url=url):
                parsed = urlsplit(url)
                self.assertEqual(parsed.netloc, urlsplit(DOMAIN).netloc, url)
                path = parsed.path
                file = ROOT / (path.lstrip('/') + 'index.html' if path.endswith('/') else path.lstrip('/'))
                self.assertTrue(file.is_file(), f'{url}: HTML publicado inexistente: {file}')
                parser = Metadata()
                parser.feed(file.read_text(encoding='utf-8'))
                self.assertEqual(len(parser.canonicals), 1, f'{url}: canonical ausente o duplicado: {parser.canonicals}')
                self.assertEqual(normalize(parser.canonicals[0]), normalize(url), f'{url}: canonical divergente: {parser.canonicals[0]}')

if __name__ == '__main__':
    unittest.main()