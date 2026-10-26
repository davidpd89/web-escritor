import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_catalogue', ROOT / 'scripts/build-reading-catalogue.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.extend(value for key, value in attrs if key == 'href')

def links(markup):
    parser = Links()
    parser.feed(markup)
    return parser.hrefs

data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = m.validate(data, ROOT)
assert books, 'data/reading-catalogue.json: catálogo publicado vacío'
priority = {'genero': 0, 'temporada': 1, 'tematica': 2, 'epoca': 3, 'contenido': 4, 'edad': 5}
for book in books:
    cats = m.categories(data, book)
    ordered = sorted(cats, key=lambda c: (priority[c['tipo']], c['orden'], c['id']))
    expected_compact = [f"/recomendaciones/#{c['tipo']}={c['id']}" for c in ordered[:3]]
    expected_full = [f"/recomendaciones/#{c['tipo']}={c['id']}" for c in cats]
    compact = links(m.tags(cats, compact=True))
    full = links(m.tags(cats))
    assert compact == expected_compact, f'{m.url(book)}: etiquetas compactas {compact}; esperadas {expected_compact}'
    assert full == expected_full, f'{m.url(book)}: etiquetas completas {full}; esperadas {expected_full}'
print(f'PASS: prioridad y conservación de etiquetas en {len(books)} libros')