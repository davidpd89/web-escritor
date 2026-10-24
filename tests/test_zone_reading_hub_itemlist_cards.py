import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
source = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = {b['id']: b for b in source['libros'] if b['estado'] == 'publicado'}

class HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.capture = False
        self.chunks = []
        self.docs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'li' and 'data-catalogue-book' in a:
            self.cards.append(a['data-book-id'])
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.capture = True
            self.chunks = []

    def handle_data(self, text):
        if self.capture:
            self.chunks.append(text)

    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.docs.append(json.loads(''.join(self.chunks)))
            self.capture = False

p = HTML()
p.feed(html)
lists = [d for d in p.docs if d.get('@type') == 'ItemList' and d.get('@id', '').endswith('#catalogo')]
assert len(lists) == 1
entries = lists[0]['itemListElement']
assert entries and len(entries) == len(p.cards) == len(books) == lists[0]['numberOfItems']
for index, (entry, book_id) in enumerate(zip(entries, p.cards), 1):
    b = books[book_id]
    assert entry['position'] == index
    item = entry['item']
    assert item['name'] == b['titulo']
    assert item['url'] == 'https://davidportodiaz.com/recomendaciones/libros/' + b['slug'] + '/'
    assert item['image'] == 'https://davidportodiaz.com' + b['portada_local']
print('reading hub ItemList parity: OK')
