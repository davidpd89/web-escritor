import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name', '').lower() == 'robots':
            self.robots.append(a.get('content', ''))

class RecoveryIndexation(unittest.TestCase):
    def test_indexation(self):
        for name, expected in [('index.html', False), ('404.html', True), ('offline.html', True)]:
            with self.subTest(page=name):
                p = Metadata()
                p.feed((ROOT / name).read_text(encoding='utf-8'))
                self.assertTrue(p.robots, f'{name}: falta robots')
                tokens = [t.strip().lower() for value in p.robots for t in value.split(',')]
                self.assertEqual('noindex' in tokens, expected, f'{name}: robots={p.robots}')
                self.assertFalse('index' in tokens and 'noindex' in tokens, f'{name}: directivas contradictorias')

if __name__ == '__main__':
    unittest.main()