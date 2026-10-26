from pathlib import Path
from html.parser import HTMLParser
from datetime import date
import re

ROOT = Path(__file__).resolve().parents[1]

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        key = a.get('name') or a.get('property')
        if key:
            self.values[key.lower()] = a.get('content', '')

page = ROOT / 'ferias.html'
parser = Metadata()
parser.feed(page.read_text(encoding='utf-8'))
fields = ('description', 'og:description', 'twitter:description')
for field in fields:
    assert parser.values.get(field), f'{page.name}: metadato {field} vacío'

# El corpus real publicado documenta las ferias de mayo y junio de 2026.
# No se inventan nuevas convocatorias ni se presupone que deba haberlas.
last_documented = date(2026, 6, 10)
if date.today() > last_documented:
    for field in fields:
        value = parser.values[field]
        assert not re.search(r'\b(próximas?|ven(?:id|ider)as?|este fin de semana|mañana)\b', value, re.I), (
            f'{page.name}: {field} presenta como futura una feria histórica: {value}'
        )

assert '2026' in parser.values['description'], f'{page.name}: la descripción pierde el contexto cronológico'
print('PASS contexto temporal de metadatos de ferias')