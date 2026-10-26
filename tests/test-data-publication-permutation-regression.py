import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalogue_publication_regression', ROOT / 'scripts/build-reading-catalogue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
expected = {book['id'] for book in data['libros'] if book['estado'] == 'publicado'}
assert expected, 'data/reading-catalogue.json: no se encontraron libros publicados'

for label, records in (
    ('orden original', data['libros']),
    ('orden inverso', list(reversed(data['libros']))),
    ('orden por identificador', sorted(data['libros'], key=lambda book: book['id'])),
):
    variant = copy.deepcopy(data)
    variant['libros'] = records
    selected = module.validate(variant, ROOT)
    actual = {book['id'] for book in selected}
    assert actual == expected, f'data/reading-catalogue.json [{label}]: faltan {sorted(expected - actual)}, sobran {sorted(actual - expected)}'
    assert len(selected) == len(expected), f'data/reading-catalogue.json [{label}]: libros publicados duplicados'

print('PASS: selección publicada independiente del orden de entrada')
