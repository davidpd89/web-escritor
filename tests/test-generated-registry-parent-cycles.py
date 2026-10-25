from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
entries = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))['entries']
parents = {entry['id']: entry.get('parentId') for entry in entries}

for start in parents:
    seen = set()
    current = start
    while current is not None:
        assert current in parents, f'{start}: padre inexistente {current}'
        assert current not in seen, f'Ciclo de navegación desde {start}: {seen}'
        seen.add(current)
        current = parents[current]
print('Registry parent cycles: OK')