import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        values = dict(attrs)
        if values.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(values.get('content', ''))


class TypographicCSPFontPolicy(unittest.TestCase):
    def test_fonts_are_restricted_to_same_origin(self):
        for route in ('index.html', '404.html'):
            with self.subTest(route=route):
                parser = MetaParser()
                parser.feed((ROOT / route).read_text(encoding='utf-8'))
                self.assertTrue(parser.policies, f'{route}: falta CSP')
                for policy in parser.policies:
                    directives = {}
                    for item in policy.split(';'):
                        tokens = item.strip().split()
                        if tokens:
                            directives[tokens[0].lower()] = tokens[1:]
                    sources = directives.get('font-src', directives.get('default-src', []))
                    self.assertIn("'self'", sources, f'{route}: fuentes propias bloqueadas: {sources}')
                    self.assertEqual(sources, ["'self'"], f'{route}: política de fuentes demasiado permisiva: {sources}')


if __name__ == '__main__':
    unittest.main()
