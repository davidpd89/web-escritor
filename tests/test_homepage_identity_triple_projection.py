import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.og = []
        self.jsonld = []
        self.inside = False
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonical.append(a.get('href'))
        if tag == 'meta' and a.get('property') == 'og:url':
            self.og.append(a.get('content'))
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.inside = True
            self.buffer = []

    def handle_data(self, data):
        if self.inside:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.inside:
            self.jsonld.append(json.loads(''.join(self.buffer)))
            self.inside = False

class HomepageIdentity(unittest.TestCase):
    def test_three_public_identities(self):
        p = Head()
        p.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
        self.assertEqual(len(p.canonical), 1, f'index.html: canonical={p.canonical}')
        self.assertEqual(len(p.og), 1, f'index.html: og:url={p.og}')
        self.assertEqual(p.canonical[0], p.og[0], 'index.html: canonical y og:url difieren')
        nodes = []
        for doc in p.jsonld:
            nodes.extend(doc.get('@graph', [doc]) if isinstance(doc, dict) else doc)
        websites = [n for n in nodes if isinstance(n, dict) and 'WebSite' in ([n.get('@type')] if isinstance(n.get('@type'), str) else n.get('@type', []))]
        self.assertTrue(websites, 'index.html: falta WebSite en JSON-LD')
        self.assertTrue(any(n.get('url') == p.canonical[0] for n in websites), 'index.html: WebSite.url no coincide con canonical')
        root = ET.parse(ROOT / 'sitemap.xml').getroot()
        locs = [e.text for e in root.iter() if e.tag.endswith('}loc')]
        self.assertIn(p.canonical[0], locs, f'sitemap.xml: falta canonical de index.html: {p.canonical[0]}')

if __name__ == '__main__':
    unittest.main()