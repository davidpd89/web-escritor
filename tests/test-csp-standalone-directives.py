import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('offline.html', 'video-ios-test/index.html')

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and (attrs.get('http-equiv') or '').lower() == 'content-security-policy':
            self.policies.append(attrs.get('content', ''))

class StandaloneCSP(unittest.TestCase):
    def test_directive_contract(self):
        for path in PAGES:
            with self.subTest(page=path):
                parser = MetaParser()
                parser.feed((ROOT / path).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.policies), 1, f'{path}: debe existir exactamente una CSP')
                policy = {}
                for raw in parser.policies[0].split(';'):
                    parts = raw.strip().split()
                    if parts:
                        self.assertNotIn(parts[0], policy, f'{path}: directiva CSP duplicada: {parts[0]}')
                        policy[parts[0]] = parts[1:]
                for name in ('default-src', 'script-src', 'style-src', 'img-src', 'font-src', 'connect-src', 'media-src', 'object-src', 'base-uri', 'form-action'):
                    self.assertIn(name, policy, f'{path}: falta {name}')
                self.assertEqual(policy['object-src'], ["'none'"], f'{path}: object-src debe impedir objetos ejecutables')
                self.assertEqual(policy['base-uri'], ["'self'"], f'{path}: base-uri inesperado')
                for name, sources in policy.items():
                    self.assertNotIn('*', sources, f'{path}: {name} permite origen global')
                    self.assertNotIn("'unsafe-eval'", sources, f'{path}: {name} permite evaluación dinámica')
                for name in ('script-src', 'style-src'):
                    self.assertNotIn("'unsafe-inline'", policy[name], f'{path}: {name} permite ejecución inline indiscriminada')
                for name in ('img-src', 'font-src', 'connect-src', 'media-src'):
                    self.assertIn("'self'", policy[name], f'{path}: {name} bloquea recursos propios')

if __name__ == '__main__':
    unittest.main()
