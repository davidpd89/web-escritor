from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

MONTHS = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        if a.get('property') in ('og:description', 'og:image:alt') or a.get('name') == 'description':
            self.values.append((a.get('property') or a.get('name'), a.get('content', '')))

parser = Metadata()
parser.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
assert parser.values, 'index.html: no se han encontrado metadatos editoriales'
pattern = re.compile(r'\b(\d{1,2}) de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre) de (20\d{2})\b', re.I)
found = 0
for field, text in parser.values:
    for match in pattern.finditer(text):
        day, month, year = match.groups()
        publication = date(int(year), MONTHS[month.lower()], int(day))
        assert publication <= date.today() or re.search(r'pr[oó]xim|previst|se publicar[aá]|lanzamiento futuro', text, re.I), f'index.html {field}: fecha futura presentada sin contexto de previsión: {match.group(0)}'
        found += 1
assert found > 0, 'index.html: no se ha ejercitado ninguna fecha editorial explícita'
print(f'PASS: {found} fechas editoriales de portada comprobadas')
