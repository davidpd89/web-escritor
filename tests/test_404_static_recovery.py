import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class RecoveryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.main_count = 0
        self.links = []
        self.h1_ids = []
        self.sections = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self.in_main = True
            self.main_count += 1
        if self.in_main:
            if tag == 'a':
                self.links.append(a.get('href'))
            if tag == 'h1':
                self.h1_ids.append(a.get('id'))
            if tag == 'section':
                self.sections.append(a.get('aria-labelledby'))
    def handle_endtag(self, tag):
        if tag == 'main':
            self.in_main = False

class Test404Recovery(unittest.TestCase):
    def test_static_recovery(self):
        p = RecoveryParser()
        p.feed((ROOT / '404.html').read_text(encoding='utf-8'))
        self.assertEqual(p.main_count, 1)
        self.assertIn('/', p.links)
        self.assertTrue(p.h1_ids)
        self.assertTrue(any(x in p.h1_ids for x in p.sections))

if __name__ == '__main__':
    unittest.main()