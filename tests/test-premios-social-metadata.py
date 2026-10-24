#!/usr/bin/env python3
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.canonical = []
        self.title = ''
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta':
            key = a.get('property') or a.get('name')
            if key:
                self.meta.setdefault(key, []).append(a.get('content', ''))
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a.get('href', ''))
        if tag == 'title':
            self.in_title = True
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
    def handle_data(self, data):
        if self.in_title:
            self.title += data

class AwardsMetadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = HeadParser()
        cls.page.feed((ROOT / 'premios.html').read_text(encoding='utf-8'))
    def single(self, key):
        values = self.page.meta.get(key, [])
        self.assertEqual(len(values), 1, f'{key}: esperado exactamente una vez')
        self.assertTrue(values[0].strip(), f'{key}: contenido vacío')
        return values[0]
    def test_identity(self):
        self.assertEqual(len(self.page.canonical), 1)
        self.assertEqual(self.single('og:url'), self.page.canonical[0])
        self.assertIn('premios', self.page.title.lower())
        self.assertIn('premios', self.single('og:title').lower())
        self.assertIn('premios', self.single('twitter:title').lower())
        self.assertEqual(self.single('og:locale'), 'es_ES')
        self.assertEqual(self.single('og:type'), 'website')
    def test_descriptions(self):
        for key in ('description', 'og:description', 'twitter:description'):
            self.assertGreaterEqual(len(self.single(key)), 70)
    def test_images(self):
        for key in ('og:image', 'twitter:image'):
            value = self.single(key)
            self.assertEqual(urlparse(value).scheme, 'https')
            self.assertEqual(urlparse(value).hostname, 'davidportodiaz.com')
            local = ROOT / urlparse(value).path.lstrip('/')
            self.assertTrue(local.is_file(), f'Imagen no encontrada: {local}')
        self.assertEqual(self.single('og:image'), self.single('twitter:image'))
        self.assertTrue(self.single('og:image:alt'))
        self.assertTrue(self.single('twitter:image:alt'))
        self.assertGreater(int(self.single('og:image:width')), 0)
        self.assertGreater(int(self.single('og:image:height')), 0)

if __name__ == '__main__':
    unittest.main()
