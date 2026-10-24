#!/usr/bin/env python3
import copy
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('radar_builder_mutation', ROOT / 'scripts/build-radar-opportunities.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
items = mod.load_items(ROOT / 'data/radar-opportunities.json')
watch = mod.load_watchlist(ROOT / 'data/radar-opportunities.json')
assert items, 'Dataset vacío'
today = date(2026, 10, 24)
fixture = copy.deepcopy(items[0])
fixture.update({'id': 'qa-parity-fixture-999', 'title': 'Prueba QA <paridad> & calendario', 'deadline': (today + timedelta(days=14)).isoformat(), 'verified_at': today.isoformat(), 'published': True})
mod.validate(fixture)
base = mod.public_json(items, today, watch)
changed_items = items + [fixture]
html = mod.build_html(changed_items, today, watch)
data = json.loads(mod.public_json(changed_items, today, watch))
ics = mod.build_ics(changed_items, today)
assert len(data['items']) == len(json.loads(base)['items']) + 1
assert sum(x['id'] == fixture['id'] for x in data['items']) == 1
assert 'Prueba QA &lt;paridad&gt; &amp; calendario' in html
assert 'Prueba QA <paridad> & calendario' not in html
assert 'qa-parity-fixture-999@davidportodiaz.com' in ics
assert fixture['deadline'].replace('-', '') in ics
assert fixture['source_url'] in html and fixture['source_url'] in ics
assert fixture['id'] not in base
print('OK propagación metamórfica HTML/JSON/ICS')
