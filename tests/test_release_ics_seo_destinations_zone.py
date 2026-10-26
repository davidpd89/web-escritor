#!/usr/bin/env python3
"""Contrato SEO de destinos anunciados por el calendario ICS."""
import json
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://davidportodiaz.com'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class SeoParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonicals = []
        self.directives = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonicals.append(a.get('href'))
        if tag == 'meta' and a.get('name', '').lower() in ('robots', 'googlebot'):
            self.directives.extend(x.strip().lower() for x in a.get('content', '').split(','))

class ReleaseDestinationContract(unittest.TestCase):
    def test_ics_urls_are_indexable_published_books(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        published = {b['slug']: b for b in data['libros'] if b['estado'] == 'publicado'}
        sitemap = ET.parse(ROOT / 'sitemap.xml').getroot()
        locations = {(n.text or '').strip() for n in sitemap.findall('.//s:url/s:loc', NS)}
        calendar = Calendar.from_ical((ROOT / 'recomendaciones/proximos-lanzamientos.ics').read_bytes())
        events = [component for component in calendar.walk() if component.name == 'VEVENT']
        for event in events:
            uid = str(event.get('UID', 'sin-uid'))
            with self.subTest(event=uid):
                url = str(event.get('URL', ''))
                parsed = urlsplit(url)
                self.assertEqual(parsed.scheme, 'https', f'{uid}: URL no HTTPS: {url}')
                self.assertEqual(parsed.netloc, 'davidportodiaz.com', f'{uid}: destino externo: {url}')
                self.assertFalse(parsed.query or parsed.fragment, f'{uid}: URL con parámetros o fragmento: {url}')
                prefix = '/recomendaciones/libros/'
                self.assertTrue(parsed.path.startswith(prefix) and parsed.path.endswith('/'), f'{uid}: destino fuera de fichas: {url}')
                slug = parsed.path[len(prefix):].strip('/')
                self.assertTrue(slug and '/' not in slug, f'{uid}: slug de destino inválido: {url}')
                self.assertIn(slug, published, f'{uid}: destino no publicado: {url}')
                self.assertIn(url, locations, f'{uid}: URL ausente del sitemap: {url}')
                route = ROOT / 'recomendaciones/libros' / slug / 'index.html'
                self.assertTrue(route.is_file(), f'{uid}: ficha inexistente: {route}')
                parser = SeoParser()
                parser.feed(route.read_text(encoding='utf-8'))
                self.assertEqual(parser.canonicals, [url], f'{uid}: canonical distinto de URL ICS: {url}')
                self.assertNotIn('noindex', parser.directives, f'{uid}: destino noindex: {url}')
                self.assertNotIn('none', parser.directives, f'{uid}: destino no indexable: {url}')

if __name__ == '__main__':
    unittest.main()