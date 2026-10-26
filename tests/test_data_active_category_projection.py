import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_catalogue', ROOT / 'scripts/build-reading-catalogue.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = m.validate(data, ROOT)
assert books, 'data/reading-catalogue.json: no hay libros publicados que comprobar'
for book in books:
    related = {r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == book['id']}
    expected = sorted((c for c in data['categorias'] if c['id'] in related and c['activa']), key=lambda c: (c['orden'], c['id']))
    actual = m.categories(data, book)
    assert actual == expected, f"{m.url(book)}: categorías {[(c['id'], c['activa']) for c in actual]} distintas de las activas {[(c['id'], c['activa']) for c in expected]}"
    assert len({c['id'] for c in actual}) == len(actual), f"{m.url(book)}: categorías duplicadas"
print(f'PASS: categorías activas y orden en {len(books)} libros publicados')