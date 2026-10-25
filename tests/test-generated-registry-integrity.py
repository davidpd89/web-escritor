from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
entries = data['entries']
assert entries, 'Registro vacío'

for key in ('id', 'url', 'sourceFile'):
    values = [entry[key] for entry in entries if entry.get(key)]
    duplicates = [value for value, count in Counter(values).items() if count > 1]
    assert not duplicates, f'Colisiones de {key}: {duplicates}'

ids = {entry['id'] for entry in entries}
for entry in entries:
    url = entry['url']
    parsed = urlsplit(url)
    assert url.startswith('/') and not url.startswith('//'), (entry['id'], url)
    assert not parsed.scheme and not parsed.netloc, (entry['id'], url)
    assert not parsed.query and not parsed.fragment, (entry['id'], url)
    assert '..' not in parsed.path.split('/'), (entry['id'], url)
    for field in ('parentId', 'hubId'):
        target = entry.get(field)
        assert target is None or target in ids, f'{entry["id"]}: {field} inexistente {target}'
    source = entry.get('sourceFile')
    if source:
        assert not Path(source).is_absolute(), source
        assert '..' not in Path(source).parts, source
        assert (ROOT / source).is_file(), f'Fuente inexistente: {source}'
print('Registry integrity: OK')