#!/usr/bin/env python3
"""Mutaciones locales de etiquetas para detectar inyección HTML."""
from __future__ import annotations

import importlib.util
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('reading_tags_escape_qa', ROOT / 'scripts/build-reading-catalogue.py')
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class Structure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.starts = []
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.starts.append(tag)
        if tag == 'a':
            self.links.append(dict(attrs))

    def handle_data(self, value):
        self.text.append(value)


class Escaping(unittest.TestCase):
    def test_special_characters_are_text_not_markup(self):
        cases = [
            'Fantasía & aventura',
            'Novela <histórica>',
            'Romance "oscuro"',
            "Lecturas 'especiales'",
            '<img src=x onerror=alert(1)>',
            'Ciencia & ficción <juvenil> "actual"',
        ]
        for index, label in enumerate(cases):
            with self.subTest(label=label):
                category = {
                    'id': f'categoria-{index}',
                    'slug': f'categoria-{index}',
                    'nombre': label,
                    'tipo': 'genero',
                    'orden': index,
                    'activa': True,
                }
                html = builder.tags([category])
                parser = Structure()
                parser.feed(html)
                self.assertEqual(parser.starts, ['ul', 'li', 'a'])
                self.assertEqual(len(parser.links), 1)
                self.assertEqual(set(parser.links[0]), {'href'})
                self.assertEqual(parser.links[0]['href'], f'/recomendaciones/#genero=categoria-{index}')
                self.assertEqual(''.join(parser.text), label)
                self.assertNotIn('<img ', html)


if __name__ == '__main__':
    unittest.main()
