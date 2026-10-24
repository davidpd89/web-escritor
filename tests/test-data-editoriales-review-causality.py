from __future__ import annotations
import copy
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('editorial_causality_qa', ROOT / 'scripts/build-editoriales.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
records = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers']
today = date(2099, 1, 1)

for record in records:
    if record.get('publish') is not True:
        continue
    updated = date.fromisoformat(record['page_updated_at'])
    verified = date.fromisoformat(record['verified_at'])
    assert updated >= verified, record['slug']
    mutated = copy.deepcopy(record)
    mutated['verified_at'] = (updated + timedelta(days=1)).isoformat()
    try:
        mod.validate_record(mutated, set(), today)
    except mod.ValidationError:
        continue
    raise AssertionError(f'{record["slug"]}: revisión posterior a página aceptada')

print('OK: causalidad de revisión editorial')
