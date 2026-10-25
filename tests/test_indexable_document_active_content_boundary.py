import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(a.get('content', ''))

class CSPBoundary(unittest.TestCase):
    def test_active_content_policy(self):
        for page in ('index.html', '404.html'):
            with self.subTest(page=page):
                parser = Parser()
                parser.feed((ROOT / page).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.policies), 1, f'{page}: número de CSP={len(parser.policies)}')
                directives = {}
                for part in parser.policies[0].split(';'):
                    words = part.strip().split()
                    if words:
                        self.assertNotIn(words[0], directives, f'{page}: directiva duplicada {words[0]}')
                        directives[words[0]] = words[1:]
                for required in ('default-src', 'script-src', 'object-src', 'base-uri'):
                    self.assertIn(required, directives, f'{page}: falta {required}')
                self.assertEqual(directives['object-src'], ["'none'"], f'{page}: object-src inseguro')
                self.assertNotIn("'unsafe-eval'", directives['script-src'], f'{page}: unsafe-eval')
                self.assertNotIn("'unsafe-inline'", directives['script-src'], f'{page}: scripts inline sin restricción')
                self.assertNotIn('*', directives['script-src'], f'{page}: origen universal de scripts')

if __name__ == '__main__':
    unittest.main()