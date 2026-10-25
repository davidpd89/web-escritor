import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class FairDocument(HTMLParser):
    def __init__(self):
        super().__init__()
        self.records = []
        self.links = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'section' and 'fair-record' in a.get('class', '').split():
            self.records.append(a.get('id'))
        if tag == 'a' and a.get('href', '').startswith('#feria-libro-'):
            self.links.append(a['href'][1:])

class TestFairTimeline(unittest.TestCase):
    def test_timeline_has_complete_targets(self):
        parser = FairDocument()
        parser.feed((ROOT / 'ferias.html').read_text(encoding='utf-8'))
        records = set(parser.records)
        self.assertTrue(records)
        self.assertTrue(parser.links)
        self.assertEqual(set(parser.links), records, 'Cronología y fichas de feria no coinciden')
        counts = Counter(parser.ids)
        for target in parser.links:
            with self.subTest(target=target):
                self.assertEqual(counts[target], 1, 'El destino debe ser único')

if __name__ == '__main__':
    unittest.main()
