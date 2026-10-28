#!/usr/bin/env python3
"""Detecta scripts externos bloqueantes en el mapa del sitio."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

PAGE = Path(__file__).resolve().parents[1] / 'mapa-del-sitio/index.html'


class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocking = []

    def handle_starttag(self, tag, attrs):
        if tag != 'script':
            return
        attrs = dict(attrs)
        src = attrs.get('src')
        if not src:
            return
        script_type = (attrs.get('type') or '').strip().lower()
        if script_type in ('module', 'importmap', 'application/ld+json'):
            return
        if script_type and script_type not in ('text/javascript', 'application/javascript'):
            return
        if 'defer' not in attrs and 'async' not in attrs:
            self.blocking.append(src)


class SitemapBlockingScripts(unittest.TestCase):
    def test_no_parser_blocking_external_scripts(self):
        parser = ScriptParser()
        parser.feed(PAGE.read_text(encoding='utf-8'))
        self.assertEqual(
            parser.blocking, [],
            f'/mapa-del-sitio/: scripts externos bloqueantes: {parser.blocking}',
        )


if __name__ == '__main__':
    unittest.main()
