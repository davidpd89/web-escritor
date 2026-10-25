#!/usr/bin/env python3
"""Seguridad de recursos y formularios de fichas generadas."""
from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.forms = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'script' and attributes.get('src'):
            self.scripts.append(attributes['src'])
        if tag == 'form':
            self.forms.append(attributes)


class ResourceSecurity(unittest.TestCase):
    def test_generated_pages_do_not_load_remote_scripts(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        for book in data['libros']:
            if book['estado'] != 'publicado':
                continue
            with self.subTest(book=book['id']):
                page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
                parser = Resources()
                parser.feed(page.read_text(encoding='utf-8'))
                for src in parser.scripts:
                    parsed = urlsplit(src)
                    self.assertFalse(parsed.scheme or parsed.netloc, f'Script remoto: {src}')
                    self.assertTrue(src.startswith('/'), f'Script con ruta relativa ambigua: {src}')
                    self.assertTrue((ROOT / parsed.path.lstrip('/')).is_file(), f'Script inexistente: {src}')
                for form in parser.forms:
                    action = form.get('action', '')
                    self.assertFalse(action.startswith('http://'), 'Formulario HTTP inseguro')
                    if action:
                        parsed = urlsplit(action)
                        self.assertTrue(action.startswith('/') or parsed.scheme == 'https', 'Destino de formulario no permitido')


if __name__ == '__main__':
    unittest.main()
