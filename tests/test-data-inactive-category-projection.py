import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalogue_categories_regression', ROOT / 'scripts/build-reading-catalogue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = module.validate(data, ROOT)
active = {category['id'] for category in data['categorias'] if category['activa']}
relations = {}
for relation in data['libro_categorias']:
    relations.setdefault(relation['libro_id'], set()).add(relation['categoria_id'])

checked = 0
for book in books:
    expected_ids = relations.get(book['id'], set()) & active
    projected = module.categories(data, book)
    actual_ids = {category['id'] for category in projected}
    assert actual_ids == expected_ids, f"recomendaciones/libros/{book['slug']}/: categorías esperadas {sorted(expected_ids)}, obtenidas {sorted(actual_ids)}"
    assert len(projected) == len(actual_ids), f"recomendaciones/libros/{book['slug']}/: categorías duplicadas"
    checked += 1

assert checked > 0, 'data/reading-catalogue.json: ninguna ficha publicada comprobada'
print(f'PASS: proyección de categorías activas en {checked} libros')
