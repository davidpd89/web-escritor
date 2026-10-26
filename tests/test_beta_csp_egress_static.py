import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('lectores-beta/index.html', 'lectores-beta/enviar-manuscrito/index.html')
ENDPOINT = 'https://subscribe.davidpd89.workers.dev'

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(a.get('content', ''))

class BetaCSPTest(unittest.TestCase):
    def test_csp_outbound_boundaries(self):
        for path in PAGES:
            with self.subTest(page=path):
                parser = MetaParser()
                parser.feed((ROOT / path).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.policies), 1, f'{path}: se esperaba una CSP única')
                directives = {}
                for item in parser.policies[0].split(';'):
                    parts = item.strip().split()
                    if parts:
                        self.assertNotIn(parts[0], directives, f'{path}: directiva CSP duplicada: {parts[0]}')
                        directives[parts[0]] = parts[1:]
                for key in ('default-src', 'script-src', 'connect-src', 'form-action', 'object-src', 'base-uri'):
                    self.assertIn(key, directives, f'{path}: falta {key}')
                self.assertEqual(directives['object-src'], ["'none'"], f'{path}: object-src insegura')
                self.assertEqual(directives['form-action'], ["'self'"], f'{path}: form-action permite destinos no previstos')
                self.assertIn(ENDPOINT, directives['connect-src'], f'{path}: falta el endpoint legítimo de suscripción')
                for key, values in directives.items():
                    self.assertNotIn('*', values, f'{path}: comodín global en {key}')
                    self.assertNotIn("'unsafe-eval'", values, f'{path}: evaluación dinámica en {key}')
                self.assertNotIn(ENDPOINT, directives['script-src'], f'{path}: el Worker de suscripción no debe ser fuente de scripts')

if __name__ == '__main__':
    unittest.main()
