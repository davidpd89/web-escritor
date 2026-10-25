#!/usr/bin/env python3
import copy
import importlib.util
import itertools
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('radar_tie_qa', ROOT / 'scripts/build-radar-opportunities.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

source = json.loads((ROOT / 'data/radar-opportunities.json').read_text(encoding='utf-8'))
seed = next(item for item in source['items'] if item.get('published') is True)
items = []
for index, title in enumerate(['Premio Zeta', 'Premio Alfa', 'Premio Beta']):
    item = copy.deepcopy(seed)
    item.update(id='qa-empate-' + str(index), title=title, deadline='2026-11-15', verified_at='2026-10-24', published=True)
    items.append(item)

today = date(2026, 10, 24)
assert len(mod.active_items(items, today)) == 3
outputs = []
for order in itertools.permutations(items):
    records = list(order)
    outputs.append((mod.build_ics(records, today), mod.public_json(records, today, []), mod.build_html(records, today, [])))
assert all(result == outputs[0] for result in outputs[1:]), 'Los empates alteran HTML, JSON o ICS'
assert outputs[0][0].count('BEGIN:VEVENT') == 3
print('PASS: empates reproducibles en los tres formatos')
