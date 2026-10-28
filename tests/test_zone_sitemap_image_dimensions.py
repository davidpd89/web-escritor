#!/usr/bin/env python3
"""Control de reserva de espacio para imágenes del mapa."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

PAGE = Path(__file__).resolve().parents[1] / 'mapa-del-sitio/index.html'


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.main_depth = 0
        self.invalid = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main':
            self.main_depth += 1
        if not self.main_depth or tag != 'img':
            return
        src = attrs.get('src', '(sin src)')
        try:
            dimensions = float(attrs.get('width', 0)) > 0 and float(attrs.get('height', 0)) > 0
        except (TypeError, ValueError):
            dimensions = False
        style = attrs.get('style') or ''
        ratio = re.search(r'(?:^|;)\s*aspect-ratio\s*:\s*(?:[1-9]\d*(?:\.\d+)?\s*/\s*[1-9]\d*(?:\.\d+)?|[1-9]\d*(?:\.\d+)?)', style, re.I)
        if not dimensions and not ratio:
            self.invalid.append(src)

    def handle_endtag(self, tag):
        if tag == 'main' and self.main_depth:
            self.main_depth -= 1


class SitemapImageDimensions(unittest.TestCase):
    def test_images_reserve_layout_space(self):
        parser = Images()
        parser.feed(PAGE.read_text(encoding='utf-8'))
        self.assertFalse(
            parser.invalid,
            f'/mapa-del-sitio/: imágenes sin dimensiones ni relación de aspecto explícita: {parser.invalid}',
        )


if __name__ == '__main__':
    unittest.main()
