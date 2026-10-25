#!/usr/bin/env python3
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class NavigationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
    def handle_starttag(self, tag, attrs):
        if tag in ('a', 'form', 'base'):
            self.elements.append((tag, dict(attrs)))

class EmbedNavigationSafety(unittest.TestCase):
    def test_destinations(self):
        parser = NavigationParser()
        parser.feed((ROOT / 'asistente/embed.html').read_text(encoding='utf-8'))
        for tag, attrs in parser.elements:
            value = attrs.get('href' if tag == 'a' else 'action', '')
            if not value:
                continue
            with self.subTest(tag=tag, destination=value):
                parsed = urlsplit(value.strip())
                self.assertNotIn(parsed.scheme.lower(), ('javascript', 'data', 'vbscript'))
                self.assertFalse(value.strip().startswith('//'))
                if parsed.scheme in ('http', 'https'):
                    self.assertEqual(parsed.hostname, 'davidportodiaz.com')
        forms = [attrs for tag, attrs in parser.elements if tag == 'form']
        self.assertEqual(len(forms), 1)
        self.assertFalse(forms[0].get('action'))
        self.assertTrue(any(tag == 'base' and attrs.get('target') == '_top' for tag, attrs in parser.elements))

if __name__ == '__main__':
    unittest.main()