import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_catalogue', ROOT / 'scripts/build-reading-catalogue.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = m.validate(data, ROOT)
assert books, 'data/reading-catalogue.json: catálogo publicado vacío'
with_synopsis = 0
with_fallback = 0
for book in books:
    expected = book.get('sinopsis_breve') or book['descripcion_breve']
    actual = m.synopsis(book)
    assert actual == expected, f"{m.url(book)}: sinopsis distinta del campo editorial seleccionado"
    assert isinstance(actual, str) and actual.strip(), f'{m.url(book)}: sinopsis vacía'
    if book.get('sinopsis_breve'):
        with_synopsis += 1
        assert book.get('sinopsis_tipo') in {'extracto_editorial', 'resumen_propio'}, f'{m.url(book)}: sinopsis sin tipo editorial'
        assert m.https(book.get('sinopsis_fuente_url')), f'{m.url(book)}: sinopsis sin fuente HTTPS'
    else:
        with_fallback += 1
print(f'PASS: {len(books)} sinopsis; {with_synopsis} específicas y {with_fallback} descripciones alternativas')