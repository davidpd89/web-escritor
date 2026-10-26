import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalogue_calendar_regression', ROOT / 'scripts/build-reading-catalogue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = module.validate(data, ROOT)
assert books, 'data/reading-catalogue.json: no hay libros publicados'

baseline = module.render_release_ics(books)
variants = {
    'orden inverso': list(reversed(books)),
    'orden por identificador': sorted(books, key=lambda book: book['id']),
    'orden por título': sorted(books, key=lambda book: book['titulo'].casefold()),
}

for label, variant in variants.items():
    actual = module.render_release_ics(variant)
    assert actual == baseline, f'Calendario de recomendaciones [{label}]: el contenido ICS depende del orden del JSON'
    assert actual.count('BEGIN:VEVENT') == actual.count('END:VEVENT'), f'Calendario de recomendaciones [{label}]: eventos ICS incompletos'

assert baseline.startswith('BEGIN:VCALENDAR'), 'Calendario de recomendaciones: falta BEGIN:VCALENDAR'
assert 'END:VCALENDAR' in baseline, 'Calendario de recomendaciones: falta END:VCALENDAR'
print('PASS: calendario de lanzamientos determinista ante permutaciones')
