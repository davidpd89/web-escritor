import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.buttons = []
        self.status = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'button':
            self.current = {'attrs': a, 'text': ''}
        if a.get('data-status') is not None or 'data-status' in a:
            self.status.append(a)
    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data
    def handle_endtag(self, tag):
        if tag == 'button' and self.current is not None:
            self.buttons.append(self.current)
            self.current = None

class TestOfflineControls(unittest.TestCase):
    def test_controls_and_live_region(self):
        p = Elements()
        p.feed((ROOT / 'offline.html').read_text(encoding='utf-8'))
        self.assertEqual(len(p.buttons), 2)
        for button in p.buttons:
            self.assertEqual(button['attrs'].get('type'), 'button')
            self.assertTrue(button['text'].strip() or button['attrs'].get('aria-label'))
        self.assertEqual(len(p.status), 1)
        self.assertEqual(p.status[0].get('role'), 'status')
        self.assertEqual(p.status[0].get('aria-live'), 'polite')

if __name__ == '__main__':
    unittest.main()