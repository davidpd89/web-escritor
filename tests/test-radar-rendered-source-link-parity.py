#!/usr/bin/env python3
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Cards(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.title = None
        self.links = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'article' and 'data-radar-item' in d:
            self.depth = 1
            self.title = d.get('data-title', '')
        elif self.depth:
            if tag == 'article':
                self.depth += 1
            if tag == 'a' and 'data-radar-source' in d:
                self.links.append((self.title, d.get('href', '')))
    def handle_endtag(self, tag):
        if tag == 'article' and self.depth:
            self.depth -= 1
            if not self.depth:
                self.title = None

data = json.loads((ROOT / 'convocatorias-escritores/opportunities.json').read_text(encoding='utf-8'))
items = data.get('items', []) + data.get('watchlist', []) + data.get('expired', [])
expected = Counter((item['title'].lower(), item['source_url']) for item in items)
parser = Cards()
parser.feed((ROOT / 'convocatorias-escritores/index.html').read_text(encoding='utf-8'))
actual = Counter(parser.links)
assert expected, 'Radar generado vacío'
assert actual == expected, f'Enlaces faltantes: {list((expected - actual).items())[:15]}\nEnlaces sobrantes: {list((actual - expected).items())[:15]}'
print(f'PASS radar source parity: {sum(actual.values())} enlaces')
