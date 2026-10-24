#!/usr/bin/env python3
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'article' and 'data-radar-item' in d:
            self.current = {'title': d.get('data-title'), 'deadline': d.get('data-deadline'), 'type': d.get('data-type'), 'organizer': d.get('data-organizer'), 'genres': d.get('data-genres'), 'kind': d.get('data-radar-kind', 'active'), 'url': None}
        elif tag == 'a' and self.current is not None and 'data-radar-source' in d:
            self.current['url'] = d.get('href')
    def handle_endtag(self, tag):
        if tag == 'article' and self.current is not None:
            self.rows.append(self.current)
            self.current = None

payload = json.loads((ROOT / 'convocatorias-escritores/opportunities.json').read_text(encoding='utf-8'))
parser = Cards()
parser.feed((ROOT / 'convocatorias-escritores/index.html').read_text(encoding='utf-8'))
expected = []
for key, kind in [('items', 'active'), ('watchlist', 'watch'), ('expired', 'expired')]:
    for item in payload.get(key, []):
        expected.append({'title': item['title'].lower(), 'deadline': '' if kind == 'watch' else item['deadline'], 'type': item['type'], 'organizer': item['organizer'].lower(), 'genres': '|'.join(item['genres']).lower(), 'kind': kind, 'url': item['source_url']})
freeze = lambda rows: Counter(tuple(sorted(row.items())) for row in rows)
assert expected, 'El JSON público no contiene fichas'
assert freeze(parser.rows) == freeze(expected), 'Las fichas HTML no reproducen el JSON público: ' + str(freeze(expected) - freeze(parser.rows))[:1200]
print(f'OK fichas radar: {len(expected)} tarjetas verificadas')
