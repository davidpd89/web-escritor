#!/usr/bin/env python3
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])

class InternalLinks(unittest.TestCase):
    def test_destinations(self):
        page = Document()
        page.feed((ROOT / 'premios.html').read_text(encoding='utf-8'))
        self.assertGreater(len(page.links), 10)
        checked = 0
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc or href.startswith('//'):
                continue
            if not url.path and not url.fragment:
                continue
            path = unquote(url.path)
            if path.startswith('/'):
                target = ROOT / path.lstrip('/')
            elif path:
                target = ROOT / path
            else:
                target = ROOT / 'premios.html'
            if target.is_dir():
                target = target / 'index.html'
            self.assertTrue(target.is_file(), f'Destino inexistente: {href} -> {target}')
            checked += 1
            if url.fragment and target.suffix.lower() in ('.html', '.htm'):
                destination = Document()
                destination.feed(target.read_text(encoding='utf-8'))
                self.assertIn(unquote(url.fragment), destination.ids, f'Fragmento inexistente: {href}')
        self.assertGreater(checked, 0)

if __name__ == '__main__':
    unittest.main()
