import re
import unittest
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []

    def handle_starttag(self, tag, attrs):
        if tag not in ('article', 'div', 'li'):
            return
        data = dict(attrs)
        if 'data-catalogue-book' in data:
            self.cards.append(data)

class RecommendationSemantics(unittest.TestCase):
    def test_card_metadata(self):
        parser = Cards()
        parser.feed((ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8'))
        self.assertGreater(len(parser.cards), 0)
        seen = set()
        for card in parser.cards:
            identity = card.get('data-book-id')
            self.assertTrue(identity, 'Libro sin identificador')
            self.assertNotIn(identity, seen, f'Libro duplicado: {identity}')
            seen.add(identity)
            pvp = card.get('data-pvp', '')
            if pvp:
                self.assertRegex(pvp, r'^\d+$', f'PVP no entero: {identity}')
                self.assertGreater(int(pvp), 0, f'PVP no positivo: {identity}')
            published = card.get('data-published', '')
            month = card.get('data-published-month', '')
            year = card.get('data-year', '')
            if published:
                self.assertRegex(published, r'^\d{4}-\d{2}-\d{2}$')
                date.fromisoformat(published)
            if month:
                self.assertRegex(month, r'^\d{4}-\d{2}$')
                date.fromisoformat(month + '-01')
            if year:
                self.assertRegex(year, r'^\d{4}$')
                date(int(year), 1, 1)
            if published and month:
                self.assertEqual(published[:7], month)
            if published and year:
                self.assertEqual(published[:4], year)

if __name__ == '__main__':
    unittest.main()