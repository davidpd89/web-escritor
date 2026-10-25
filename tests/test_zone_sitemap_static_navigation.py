#!/usr/bin/env python3
"""Protege la navegación estática del mapa del sitio."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'mapa-del-sitio/index.html'


class MainLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.main_depth = 0
        self.links = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main':
            self.main_depth += 1
        if self.main_depth and tag == 'a' and attrs.get('href'):
            self.links.add(attrs['href'].split('#')[0])

    def handle_endtag(self, tag):
        if tag == 'main' and self.main_depth:
            self.main_depth -= 1


class SitemapStaticNavigation(unittest.TestCase):
    def test_main_sections_are_available_without_javascript(self):
        parser = MainLinks()
        parser.feed(PAGE.read_text(encoding='utf-8'))
        required = {
            '/libros/',
            '/cuaderno/',
            '/recomendaciones/',
            '/herramientas/',
        }
        for route in sorted(required):
            with self.subTest(route=route):
                self.assertIn(
                    route, parser.links,
                    f'/mapa-del-sitio/: falta el enlace HTML estático {route} dentro del contenido principal',
                )
                target = ROOT / route.lstrip('/') / 'index.html'
                self.assertTrue(
                    target.is_file(),
                    f'/mapa-del-sitio/: el destino {route} no tiene index.html en el repositorio',
                )


if __name__ == '__main__':
    unittest.main()
