from __future__ import annotations
import copy
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('editoriales_slug_collision', ROOT / 'scripts/build-editoriales.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
records = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers']
assert records
base = records[0]
today = max(date.fromisoformat(record['verified_at']) for record in records)
for slug in ['Nombre Editorial', '../escape', 'editorial/', 'editorial--doble', 'editorial_otra', 'área', 'UPPER']:
    record = copy.deepcopy(base)
    record['slug'] = slug
    try:
        module.validate_record(record, set(), today)
    except module.ValidationError:
        pass
    else:
        raise AssertionError(f'Slug inválido admitido: {slug}')
seen = {base['slug']}
try:
    module.validate_record(copy.deepcopy(base), seen, today)
except module.ValidationError:
    pass
else:
    raise AssertionError('Slug duplicado admitido')
print('editoriales slug collision: OK')
