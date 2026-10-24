import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
public = json.loads((ROOT / 'convocatorias-escritores/opportunities.json').read_text(encoding='utf-8'))

class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article' and 'data-radar-item' in a:
            kind = a.get('data-radar-kind', 'active')
            self.rows.append((kind, a.get('data-title'), a.get('data-organizer'),
                              a.get('data-deadline'), a.get('data-verified-at'), a.get('data-type')))

parser = Cards()
parser.feed((ROOT / 'convocatorias-escritores/index.html').read_text(encoding='utf-8'))

def identity(kind, row):
    return (kind, row['title'].lower(), row['organizer'].lower(),
            '' if kind == 'watch' else row['deadline'], row['verified_at'], row['type'])

expected = Counter(identity(kind, row) for key, kind in
                   [('items', 'active'), ('watchlist', 'watch'), ('expired', 'expired')]
                   for row in public[key])
assert expected, 'Radar público sin registros: revisar fixture'
assert Counter(parser.rows) == expected, 'Diferencia de fichas entre JSON y HTML'
print('radar HTML/JSON cards: OK')
