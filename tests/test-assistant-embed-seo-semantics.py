#!/usr/bin/env python3
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.meta = []
        self.titles = []
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == 'meta':
            self.meta.append(attrs)
        if tag == 'title':
            self.in_title = True
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
    def handle_data(self, data):
        if self.in_title:
            self.titles.append(data)

class EmbedSeoSemantics(unittest.TestCase):
    def test_embed_document(self):
        parser = DocumentParser()
        parser.feed((ROOT / 'asistente/embed.html').read_text(encoding='utf-8'))
        self.assertEqual(sum(tag == 'html' for tag, _ in parser.tags), 1)
        self.assertEqual(sum(tag == 'main' for tag, _ in parser.tags), 1)
        self.assertEqual(sum(tag == 'h1' for tag, _ in parser.tags), 1)
        self.assertTrue(''.join(parser.titles).strip())
        robots = [item.get('content', '') for item in parser.meta if item.get('name', '').lower() == 'robots']
        self.assertEqual(len(robots), 1)
        directives = {part.strip().lower() for part in robots[0].split(',')}
        self.assertIn('noindex', directives)
        self.assertIn('nofollow', directives)
        html = next(attrs for tag, attrs in parser.tags if tag == 'html')
        self.assertEqual(html.get('lang'), 'es')
        self.assertTrue(any(tag == 'base' and attrs.get('target') == '_top' for tag, attrs in parser.tags))

    def test_standalone_canonical(self):
        source = (ROOT / 'asistente/index.html').read_text(encoding='utf-8')
        self.assertRegex(source, r'<link\s+rel="canonical"\s+href="https://davidportodiaz\.com/asistente/"')
        self.assertRegex(source, r'<meta\s+name="robots"\s+content="noindex,nofollow"')

if __name__ == '__main__':
    unittest.main()