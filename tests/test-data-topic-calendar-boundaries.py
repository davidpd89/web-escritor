from __future__ import annotations
import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('topic_dates_qa', ROOT / 'scripts/build-topic-collections.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
base = json.loads((ROOT / 'data/topic-collections.json').read_text(encoding='utf-8'))
assert mod.validate(copy.deepcopy(base))

valid = ['2024-02-29', '2026-02-28', '2026-12-31', '2026-01-01']
invalid = ['2025-02-29', '2026-02-30', '2026-04-31', '2026-13-01', '2026-00-01', '2026-01-00']

for stamp in valid:
    payload = copy.deepcopy(base)
    payload['collections'][0]['updated'] = stamp
    mod.validate(payload)

for stamp in invalid:
    payload = copy.deepcopy(base)
    payload['collections'][0]['updated'] = stamp
    try:
        mod.validate(payload)
    except (mod.ValidationError, ValueError):
        continue
    raise AssertionError(f'Fecha imposible aceptada: {stamp}')

print('OK: fechas civiles y límites bisiestos')
