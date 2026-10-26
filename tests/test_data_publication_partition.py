import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_catalogue', ROOT / 'scripts/build-reading-catalogue.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
all_books = data['libros']
assert all_books, 'data/reading-catalogue.json: no hay libros'
assert all(book['estado'] in {'publicado', 'listo', 'borrador'} for book in all_books), 'data/reading-catalogue.json: estado editorial desconocido'
expected = [book['id'] for book in all_books if book['estado'] == 'publicado']
actual_books = m.validate(data, ROOT)
actual = [book['id'] for book in actual_books]
assert actual == expected, f'data/reading-catalogue.json: IDs públicos {actual}; esperados {expected}'
assert len(actual) == len(set(actual)), 'data/reading-catalogue.json: libro publicado duplicado'
for book in actual_books:
    assert m.url(book) == f"/recomendaciones/libros/{book['slug']}/", f"{book['id']}: destino público incorrecto"
for book in all_books:
    if book['estado'] != 'publicado':
        assert book['id'] not in actual, f"{book['id']}: estado {book['estado']} filtrado incorrectamente"
print(f'PASS: partición editorial {dict(Counter(b["estado"] for b in all_books))}')