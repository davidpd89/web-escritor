import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'convocatorias-escritores'


class Cards(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards = []
        self.current = None
        self.depth = 0
        self.heading = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article' and 'radar-card' in a.get('class', '').split():
            self.current = {'title': '', 'url': None, 'kind': a.get('data-radar-kind', '')}
            self.depth = 1
        elif self.current is not None:
            if tag not in ('br', 'img', 'input', 'meta', 'link', 'hr', 'source', 'wbr'):
                self.depth += 1
            if tag == 'h2':
                self.heading = True
            if tag == 'a' and 'data-radar-source' in a:
                self.current['url'] = a.get('href')

    def handle_data(self, data):
        if self.current is not None and self.heading:
            self.current['title'] += data

    def handle_endtag(self, tag):
        if self.current is None:
            return
        if tag == 'h2':
            self.heading = False
        self.depth -= 1
        if self.depth == 0:
            self.cards.append(self.current)
            self.current = None


class RadarSourceDestinations(unittest.TestCase):
    def test_published_destinations(self):
        data = json.loads((BASE / 'opportunities.json').read_text(encoding='utf-8'))
        parser = Cards()
        parser.feed((BASE / 'index.html').read_text(encoding='utf-8'))
        actual = {}
        for card in parser.cards:
            actual.setdefault(card['title'].strip(), []).append(card)
        checked = 0
        for item in data.get('items', []) + data.get('watchlist', []):
            if not item.get('published'):
                continue
            matches = actual.get(item['title'], [])
            self.assertEqual(len(matches), 1, f"/convocatorias-escritores/: {item['id']} tiene {len(matches)} fichas")
            self.assertEqual(matches[0]['url'], item['source_url'], f"/convocatorias-escritores/: destino incorrecto de {item['id']}")
            checked += 1
        self.assertGreater(checked, 0, '/convocatorias-escritores/: no se verificaron convocatorias')


if __name__ == '__main__':
    unittest.main()
