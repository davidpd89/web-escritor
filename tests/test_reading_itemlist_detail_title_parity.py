import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
HOST = 'davidportodiaz.com'

class JSONLD(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type', '').lower() == 'application/ld+json':
            self.active = True
            self.blocks.append('')

    def handle_data(self, data):
        if self.active:
            self.blocks[-1] += data

    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

def read_nodes(path):
    parser = JSONLD()
    parser.feed(path.read_text(encoding='utf-8'))
    for block in parser.blocks:
        data = json.loads(block)
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict):
                yield from item.get('@graph', [item])

hub = ROOT / 'recomendaciones/index.html'
itemlists = [n for n in read_nodes(hub) if n.get('@type') == 'ItemList' and n.get('itemListElement')]
assert len(itemlists) == 1, f'{hub}: se esperaba un ItemList principal'
entries = itemlists[0]['itemListElement']
assert entries, f'{hub}: ItemList sin libros'
checked = 0
for entry in entries:
    item = entry.get('item', {})
    if not isinstance(item, dict) or item.get('@type') != 'Book':
        continue
    url = item.get('url', '')
    parsed = urlsplit(url)
    assert parsed.scheme == 'https' and parsed.hostname == HOST, f'{hub}: destino no canónico {url!r}'
    assert parsed.path.startswith('/recomendaciones/libros/') and parsed.path.endswith('/'), f'{hub}: ruta bibliográfica inesperada {url!r}'
    path = ROOT / parsed.path.lstrip('/') / 'index.html'
    assert path.is_file(), f'{hub}: libro {item.get("name")!r} enlaza a ficha inexistente {path}'
    books = [node for node in read_nodes(path) if node.get('@type') == 'Book' and node.get('url') == url]
    assert len(books) == 1, f'{path}: Book canónico ausente o duplicado para {url}'
    assert books[0].get('name') == item.get('name'), f'{path}: título {books[0].get("name")!r} distinto del ItemList {item.get("name")!r}'
    checked += 1
assert checked > 0, f'{hub}: no se verificaron libros del ItemList'
print(f'PASS: paridad de {checked} títulos entre ItemList y fichas')
