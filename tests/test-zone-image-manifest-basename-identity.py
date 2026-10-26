from pathlib import Path
from collections import defaultdict
import json

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'data/image-format-ladder.json').read_text(encoding='utf-8'))
entries = manifest['eligible_sources']
assert entries, 'data/image-format-ladder.json: no hay fuentes elegibles'

for field in ('source', 'derivative'):
    names = defaultdict(list)
    for entry in entries:
        value = entry[field]
        names[Path(value).name.casefold()].append(value)
    collisions = {name: paths for name, paths in names.items() if len(paths) > 1}
    assert not collisions, f'data/image-format-ladder.json: colisiones en {field}: {collisions}'

print('PASS image manifest basename identity')