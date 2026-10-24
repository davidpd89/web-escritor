from pathlib import Path
from html.parser import HTMLParser
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
MONTHS = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')

class Times(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []
        self.active = False
    def handle_starttag(self, tag, attrs):
        if tag == 'time':
            self.values.append([dict(attrs).get('datetime', ''), ''])
            self.active = True
    def handle_data(self, data):
        if self.active:
            self.values[-1][1] += data
    def handle_endtag(self, tag):
        if tag == 'time':
            self.active = False

html = (ROOT / 'lecturas/index.html').read_text(encoding='utf-8')
assert 'lang="es"' in html, 'Unexpected document language'
p = Times()
p.feed(html)
assert p.values, 'No dates to localize'
for raw, label in p.values:
    d = date.fromisoformat(raw)
    expected = f'{d.day} de {MONTHS[d.month - 1]} de {d.year}'
    assert expected in label.casefold(), f'{raw}: expected Spanish label {expected!r}, got {label!r}'
print(f'PASS {len(p.values)} localized date labels')
