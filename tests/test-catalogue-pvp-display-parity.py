from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Prices(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.current = None
        self.collecting = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'li' and 'data-catalogue-book' in a:
            self.current = {'id': a.get('data-book-id'), 'cents': a.get('data-pvp'), 'label': ''}
            self.cards.append(self.current)
        elif tag == 'span' and self.current:
            if 'catalogue-pvp' in (a.get('class') or '').split():
                self.collecting = True

    def handle_data(self, data):
        if self.collecting and self.current:
            self.current['label'] += data

    def handle_endtag(self, tag):
        if tag == 'span' and self.collecting:
            self.collecting = False

class PvpParity(unittest.TestCase):
    def test_display_matches_filter_integer(self):
        parser = Prices()
        parser.feed((ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8'))
        self.assertGreater(len(parser.cards), 50)
        for card in parser.cards:
            with self.subTest(book=card['id']):
                self.assertTrue((card['cents'] or '').isdigit())
                cents = int(card['cents'])
                self.assertGreater(cents, 0)
                expected = f'{cents // 100:,}'.replace(',', '.') + f',{cents % 100:02d} €'
                self.assertEqual(card['label'].strip().replace('\u00a0', ' '), expected)

if __name__ == '__main__':
    unittest.main()