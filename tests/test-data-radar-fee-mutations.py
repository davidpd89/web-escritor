from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('radar_fee_qa', ROOT / 'scripts/build-radar-opportunities.py')
radar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radar)
source = json.loads((ROOT / 'data/radar-opportunities.json').read_text(encoding='utf-8'))['items'][0]

accepted = [None, 0, 0.01, 1, 19.99, 1000]
rejected = [-1, -0.01, 0.001, 1.999, float('nan'), float('inf'), -float('inf'), True, False, '0', '', [], {}]

for value in accepted:
    item = copy.deepcopy(source)
    item['fee_eur'] = value
    radar.validate(item)

for value in rejected:
    item = copy.deepcopy(source)
    item['fee_eur'] = value
    try:
        radar.validate(item)
    except (ValueError, TypeError, OverflowError):
        continue
    raise AssertionError(f'Se aceptó una tasa monetaria inválida: {value!r}')

print(f'OK: {len(accepted)} valores admitidos y {len(rejected)} mutaciones rechazadas')
