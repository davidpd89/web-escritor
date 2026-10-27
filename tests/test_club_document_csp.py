from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    'clubes-de-lectura/preparar-sesion/index.html',
    'clubes-de-lectura/samuel-entre-mundos/index.html',
    'clubes-de-lectura/samuel-entre-mundos/guia-imprimible/index.html',
]

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        data = dict(attrs)
        if data.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(data.get('content', ''))

class CSPTests(unittest.TestCase):
    def test_public_documents_have_restrictive_csp(self):
        for relative in PAGES:
            with self.subTest(page=relative):
                parser = MetaParser()
                parser.feed((ROOT / relative).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.policies), 1, f'{relative}: se espera una única CSP documental')
                directives = {}
                for part in parser.policies[0].split(';'):
                    tokens = part.strip().split()
                    if tokens:
                        self.assertNotIn(tokens[0], directives, f'{relative}: directiva CSP duplicada {tokens[0]}')
                        directives[tokens[0]] = tokens[1:]
                for directive in ('default-src', 'script-src', 'object-src', 'base-uri'):
                    self.assertIn(directive, directives, f'{relative}: falta {directive}')
                self.assertEqual(directives['object-src'], ["'none'"], f'{relative}: object-src inseguro')
                self.assertTrue(set(directives['base-uri']) <= {"'self'", "'none'"}, f'{relative}: base-uri demasiado amplio')
                self.assertFalse({'*', "'unsafe-inline'", "'unsafe-eval'"} & set(directives['script-src']), f'{relative}: script-src inseguro')

if __name__ == '__main__':
    unittest.main()
