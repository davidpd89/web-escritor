from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'autor.html', 'prensa.html', 'premios.html']

class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.descriptions = []
        self.robots = []
        self.in_title = False
        self.title_count = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title':
            self.in_title = True
            self.title_count += 1
        if tag == 'meta':
            name = a.get('name', '').lower()
            if name == 'description': self.descriptions.append(a.get('content', ''))
            if name == 'robots': self.robots.append(a.get('content', ''))
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.title_parts.append(data)

def norm(value):
    return re.sub(r'\s+', ' ', value).strip().casefold()

seen_titles = {}
seen_descriptions = {}
checked = 0
for route in PAGES:
    p = Head()
    p.feed((ROOT / route).read_text(encoding='utf-8'))
    directives = {x.strip().lower() for value in p.robots for x in value.split(',')}
    if 'noindex' in directives:
        continue
    title = norm(''.join(p.title_parts))
    assert p.title_count == 1 and title, f'{route}: title inválido: {title!r}'
    assert len(p.descriptions) == 1 and norm(p.descriptions[0]), f'{route}: description inválida: {p.descriptions!r}'
    description = norm(p.descriptions[0])
    assert title not in seen_titles, f'{route}: title duplicado con {seen_titles.get(title)}: {title!r}'
    assert description not in seen_descriptions, f'{route}: description duplicada con {seen_descriptions.get(description)}: {description!r}'
    seen_titles[title] = route
    seen_descriptions[description] = route
    checked += 1
assert checked >= 2, f'Muestra institucional insuficiente: {checked} documentos indexables'
print(f'OK: {checked} documentos institucionales con metadatos diferenciados')