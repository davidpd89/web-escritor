#!/usr/bin/env python3
"""Indexabilidad de fichas generadas y pertenencia al sitemap."""
import json
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://davidportodiaz.com'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class IndexParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonicals = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonicals.append(a.get('href'))
        if tag == 'meta' and a.get('name', '').lower() in ('robots', 'googlebot'):
            self.robots.append(a.get('content', ''))

class SitemapIndexability(unittest.TestCase):
    def test_published_routes(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        root = ET.parse(ROOT / 'sitemap.xml').getroot()
        counts = Counter((node.text or '').strip() for node in root.findall('.//s:url/s:loc', NS))
        published = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.assertTrue(published, 'No hay libros publicados que comprobar')
        for book in data['libros']:
            url = f'{SITE}/recomendaciones/libros/{book["slug"]}/'
            route = f'recomendaciones/libros/{book["slug"]}/index.html'
            with self.subTest(page=route, estado=book['estado']):
                if book['estado'] != 'publicado':
                    self.assertEqual(counts[url], 0, f'{route}: ficha no publicada en sitemap')
                    continue
                self.assertEqual(counts[url], 1, f'{route}: apariciones en sitemap: {counts[url]}')
                self.assertTrue((ROOT / route).is_file(), f'{route}: ficha publicada ausente')
                parser = IndexParser()
                parser.feed((ROOT / route).read_text(encoding='utf-8'))
                self.assertEqual(parser.canonicals, [url], f'{route}: canonical no coincide con sitemap')
                directives = [x.strip().lower() for content in parser.robots for x in content.split(',')]
                self.assertNotIn('noindex', directives, f'{route}: robots impide indexación')
                self.assertNotIn('none', directives, f'{route}: robots impide indexación')
        prefix = SITE + '/recomendaciones/libros/'
        expected = {f'{prefix}{b["slug"]}/' for b in published}
        actual = {url for url in counts if url.startswith(prefix)}
        self.assertEqual(actual, expected, f'Sitemap: fichas sobrantes={sorted(actual-expected)}, ausentes={sorted(expected-actual)}')

if __name__ == '__main__':
    unittest.main()