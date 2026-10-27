import importlib.util
import json
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('reading_dates', ROOT / 'scripts/build-reading-list.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
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

source = json.loads((ROOT / 'data/reading-list.json').read_text(encoding='utf-8'))
item = dict(source['items'][0])
item.update(publish=True, link_kind='none', url=None, status='reading', started_on='2026-07-01')
items, disclosure = mod.validate({'items': [item], 'affiliate_disclosure': source['affiliate_disclosure']}, date(2026, 10, 26))
rendered = mod.render(items, disclosure, '2026-08-19')
parser = Times()
parser.feed(rendered)
assert len(parser.values) >= 2, f'lecturas/index.html: se esperaban fecha de actualización e inicio, obtenidas {parser.values!r}'
for raw, label in parser.values:
    day = date.fromisoformat(raw)
    expected = f'{day.day} de {MONTHS[day.month - 1]} de {day.year}'
    assert label.strip().casefold() == expected, f'lecturas/index.html: datetime={raw!r}, etiqueta visible={label!r}, esperado={expected!r}'
print('PASS generated Spanish reading dates')