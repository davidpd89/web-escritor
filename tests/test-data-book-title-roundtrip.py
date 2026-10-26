import html
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalogue_titles_regression', ROOT / 'scripts/build-reading-catalogue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, value):
        self.parts.append(value)

data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = module.validate(data, ROOT)
assert books, 'data/reading-catalogue.json: no hay títulos publicados para comprobar'

for book in books:
    rendered = module.book_title(book)
    collector = TextCollector()
    collector.feed(rendered)
    actual = html.unescape(''.join(collector.parts))
    expected = book['titulo']
    assert actual == expected, f"recomendaciones/libros/{book['slug']}/: título original {expected!r}, título representado {actual!r}"

print(f'PASS: conservación de títulos bibliográficos en {len(books)} libros')
