from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'convocatorias-escritores/opportunities.json'
payload = json.loads(path.read_text(encoding='utf-8'))
assert isinstance(payload, dict)
assert payload.get('generated_for'), 'Falta fecha de generación'

ids = []
for collection in ('items', 'watchlist'):
    records = payload.get(collection, [])
    assert isinstance(records, list), f'{collection} no es una lista'
    for index, record in enumerate(records):
        assert isinstance(record, dict), (collection, index)
        identifier = record.get('id')
        assert isinstance(identifier, str) and identifier.strip(), (collection, index)
        ids.append(identifier)

duplicates = [value for value, count in Counter(ids).items() if count > 1]
assert not duplicates, f'Identificadores públicos duplicados: {duplicates}'
assert ids, 'No hay entidades públicas verificables'
print('Radar public identity: OK')