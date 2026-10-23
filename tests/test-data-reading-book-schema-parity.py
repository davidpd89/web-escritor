from __future__ import annotations
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://davidportodiaz.com'
raw = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.schemas = []
        self.inside = False
        self.parts = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a.get('href'))
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.inside = True
            self.parts = []
    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self.inside:
            self.schemas.append(json.loads(''.join(self.parts)))
            self.inside = False

def flatten(value):
    if isinstance(value, list):
        for item in value:
            yield from flatten(item)
    elif isinstance(value, dict):
        yield value
        if '@graph' in value:
            yield from flatten(value['@graph'])

count = 0
for book in raw['libros']:
    if book['estado'] != 'publicado':
        continue
    url = f'/recomendaciones/libros/{book["slug"]}/'
    file = ROOT / url.lstrip('/') / 'index.html'
    assert file.is_file(), url
    parser = Metadata()
    parser.feed(file.read_text(encoding='utf-8'))
    assert parser.canonical == [SITE + url], url
    nodes = list(flatten(parser.schemas))
    books = [n for n in nodes if 'Book' in ([n.get('@type')] if isinstance(n.get('@type'), str) else n.get('@type', []))]
    assert books, f'Sin Book: {url}'
    assert any(n.get('name') == book['titulo'] for n in books), f'Nombre Book divergente: {url}'
    count += 1

print(f'OK: {count} fichas con SEO bibliográfico coherente')
