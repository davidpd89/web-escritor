import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.records = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'a' and a.get('href', '').startswith('#'):
            self.links.append(a['href'][1:])
        if tag == 'section' and 'fair-record' in a.get('class', '').split():
            self.records.append(a)

class TestFairNavigation(unittest.TestCase):
    def test_documented_fairs(self):
        parser = Structure()
        parser.feed((ROOT / 'ferias.html').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(parser.records), 2)
        for record in parser.records:
            with self.subTest(record=record.get('id')):
                self.assertIn(record.get('id'), parser.links)
                self.assertIn(record.get('id'), parser.ids)
                self.assertIn(record.get('aria-labelledby'), parser.ids)
        for fragment in ('feria-libro-aranjuez-2026', 'feria-libro-madrid-2026'):
            self.assertIn(fragment, parser.links)
        self.assertTrue((ROOT / 'eventos.html').exists())

if __name__ == '__main__':
    unittest.main()
