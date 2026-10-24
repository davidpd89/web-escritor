import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
books = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']

class LD(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture = False
        self.docs = []
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.capture = True
            self.buf = []

    def handle_data(self, s):
        if self.capture:
            self.buf.append(s)

    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.docs.append(json.loads(''.join(self.buf)))
            self.capture = False

for b in books:
    path = ROOT / 'recomendaciones/libros' / b['slug'] / 'index.html'
    if b['estado'] != 'publicado':
        assert not path.exists(), b['id']
        continue
    assert path.is_file(), b['id']
    parser = LD()
    parser.feed(path.read_text(encoding='utf-8'))
    nodes = [x for d in parser.docs for x in d.get('@graph', [d])]
    book = next(x for x in nodes if x.get('@type') == 'Book')
    page = next(x for x in nodes if x.get('@type') == 'WebPage')
    canonical = 'https://davidportodiaz.com/recomendaciones/libros/' + b['slug'] + '/'
    assert book['url'] == canonical and book['name'] == b['titulo']
    assert [x['name'] for x in book['author']] == b['autores']
    assert book['bookEdition'] == b['edicion']
    assert book.get('isbn') == b.get('isbn13')
    assert page['dateModified'] == b['fecha_actualizacion']
    assert page['mainEntity']['@id'] == book['@id']
print('book detail Book/WebPage parity: OK')
