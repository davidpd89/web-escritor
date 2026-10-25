import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.lang = None
        self.title = ''
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'meta':
            self.meta[a.get('name', '').lower()] = a.get('content', '')
        if tag == 'title':
            self.in_title = True
    def handle_data(self, data):
        if self.in_title:
            self.title += data
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

class TestErrorSEO(unittest.TestCase):
    def test_error_metadata(self):
        for name in ('404.html', 'offline.html'):
            with self.subTest(page=name):
                p = Metadata()
                p.feed((ROOT / name).read_text(encoding='utf-8'))
                self.assertEqual(p.lang, 'es')
                self.assertIn('noindex', p.meta.get('robots', '').lower())
                self.assertGreater(len(p.title.strip()), 12)
                self.assertGreater(len(p.meta.get('description', '').strip()), 40)
                self.assertEqual(p.meta.get('theme-color'), '#ffffff')

if __name__ == '__main__':
    unittest.main()