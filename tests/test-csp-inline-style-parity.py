import base64
import hashlib
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('offline.html', 'video-ios-test/index.html')

class StyleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = False
        self.parts = []
        self.styles = []
        self.policy = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and (attrs.get('http-equiv') or '').lower() == 'content-security-policy':
            self.policy = attrs.get('content')
        if tag == 'style':
            self.active = True
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'style' and self.active:
            self.styles.append(''.join(self.parts))
            self.active = False

class CSPStyleParity(unittest.TestCase):
    def test_published_style_hashes(self):
        for path in PAGES:
            with self.subTest(page=path):
                parser = StyleParser()
                parser.feed((ROOT / path).read_text(encoding='utf-8'))
                self.assertTrue(parser.styles, f'{path}: no se encontraron estilos inline')
                self.assertIsNotNone(parser.policy, f'{path}: falta CSP')
                directives = {}
                for directive in parser.policy.split(';'):
                    tokens = directive.strip().split()
                    if tokens:
                        directives[tokens[0]] = tokens[1:]
                sources = directives.get('style-src', directives.get('default-src', []))
                for index, style in enumerate(parser.styles, 1):
                    digest = base64.b64encode(hashlib.sha256(style.encode('utf-8')).digest()).decode('ascii')
                    self.assertIn("'sha256-" + digest + "'", sources, f'{path}: style #{index} bloqueado por style-src; hash esperado sha256-{digest}')

if __name__ == '__main__':
    unittest.main()
