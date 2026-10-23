from __future__ import annotations
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'data/writer-tools.json').read_text(encoding='utf-8'))
html = (ROOT / 'recursos/herramientas-para-escritores/index.html').read_text(encoding='utf-8')

class CardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article' and 'wt-card' in a.get('class', '').split():
            self.cards.append(a)

parser = CardParser()
parser.feed(html)
expected = [t for t in source['tools'] if t['status'] != 'deprecated']
assert len(parser.cards) == len(expected)

names = [card['data-name'] for card in parser.cards]
assert len(names) == len(set(names)), 'Tarjetas duplicadas'
for tool in expected:
    name = tool['name'].lower()
    matches = [card for card in parser.cards if card['data-name'] == name]
    assert len(matches) == 1, f'{name}: tarjeta ausente o duplicada'
    card = matches[0]
    assert set(card['data-stages'].split()) == set(tool['stages']), name
    assert card['data-price'] == tool['price']['model'], name
    assert card['data-account'] == ('0' if tool['account_required'] is False else '1' if tool['account_required'] is True else 'unknown'), name

for tool in source['tools']:
    if tool['status'] == 'deprecated':
        assert tool['name'].lower() not in names
print(f'OK: {len(expected)} tarjetas sincronizadas')
