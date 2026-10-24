from pathlib import Path
from html.parser import HTMLParser
import json

ROOT = Path(__file__).resolve().parents[1]

class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.cards = []
        self.script = False
        self.heading = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.blocks.append('')
            self.script = True
        if tag == 'article':
            self.cards.append({'fixture': a.get('data-fixture') == 'true', 'title': ''})
        if tag == 'h3' and self.cards:
            self.heading = True
    def handle_data(self, data):
        if self.script:
            self.blocks[-1] += data
        if self.heading:
            self.cards[-1]['title'] += data
    def handle_endtag(self, tag):
        if tag == 'script': self.script = False
        if tag == 'h3': self.heading = False

p = Collector()
p.feed((ROOT / 'lecturas/index.html').read_text(encoding='utf-8'))
schemas = [json.loads(block) for block in p.blocks]
collection = next((s for s in schemas if s.get('@type') == 'CollectionPage'), None)
assert collection, 'Missing CollectionPage'
items = collection.get('mainEntity', {}).get('itemListElement', [])
fixture_titles = {c['title'].strip().casefold() for c in p.cards if c['fixture']}
real_titles = [c['title'].strip() for c in p.cards if not c['fixture']]
schema_titles = [str(item.get('name', '')).strip() for item in items]
assert not fixture_titles.intersection(title.casefold() for title in schema_titles), 'Fixture published as a real ListItem'
assert sorted(schema_titles) == sorted(real_titles), 'ItemList differs from real reading cards'
assert [i.get('position') for i in items] == list(range(1, len(items) + 1)), 'ItemList positions are not sequential'
print('PASS structured data excludes fixtures')
