import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('eventos.html', 'ferias.html')


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        if a.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(a.get('content', ''))


class TestEditorialCSP(unittest.TestCase):
    def test_security_directives(self):
        for path in PAGES:
            with self.subTest(page=path):
                parser = MetaParser()
                parser.feed((ROOT / path).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.policies), 1, f'{path}: debe existir una CSP única')
                directives = {}
                for part in parser.policies[0].split(';'):
                    tokens = part.strip().split()
                    if not tokens:
                        continue
                    self.assertNotIn(tokens[0], directives, f'{path}: directiva CSP duplicada: {tokens[0]}')
                    directives[tokens[0]] = tokens[1:]
                for key in ('default-src', 'script-src', 'object-src', 'base-uri', 'form-action', 'connect-src'):
                    self.assertIn(key, directives, f'{path}: falta {key}')
                self.assertEqual(directives['object-src'], ["'none'"], f'{path}: object-src inseguro')
                for key, values in directives.items():
                    self.assertNotIn('*', values, f'{path}: comodín global en {key}')
                    self.assertNotIn("'unsafe-eval'", values, f'{path}: unsafe-eval en {key}')
                self.assertNotIn("'unsafe-inline'", directives['script-src'], f'{path}: scripts inline sin restricción')
                self.assertEqual(directives['base-uri'], ["'self'"], f'{path}: base-uri ampliado')
                self.assertEqual(directives['form-action'], ["'self'"], f'{path}: form-action ampliado')


if __name__ == '__main__':
    unittest.main()