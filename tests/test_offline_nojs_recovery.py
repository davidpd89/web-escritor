import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.buttons = []
        self.noscript = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        if tag == 'button':
            self.buttons.append(a)
        if tag == 'noscript':
            self.noscript += 1

class TestOfflineNoJS(unittest.TestCase):
    def test_recovery_without_javascript(self):
        html = (ROOT / 'offline.html').read_text(encoding='utf-8')
        p = Parser()
        p.feed(html)
        self.assertTrue(p.buttons, 'Expected enhanced recovery controls')
        self.assertTrue(any(h.startswith('/') or h.startswith('#') for h in p.links), 'Offline screen has no native recovery link')
        self.assertTrue(p.noscript or 'no-js' in html)

if __name__ == '__main__':
    unittest.main()