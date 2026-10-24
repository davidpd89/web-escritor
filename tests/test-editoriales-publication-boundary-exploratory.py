from __future__ import annotations
import copy
import importlib.util
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('editoriales_publication_boundary', ROOT / 'scripts/build-editoriales.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
raw = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
published = [record for record in raw['publishers'] if record.get('publish') is True]
assert published, 'Se necesita al menos una editorial publicada'
target = published[0]['slug']
today = max(date.fromisoformat(record['verified_at']) for record in raw['publishers'])
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'editoriales.json'
    mutated = copy.deepcopy(raw)
    next(record for record in mutated['publishers'] if record['slug'] == target)['publish'] = False
    path.write_text(json.dumps(mutated, ensure_ascii=False), encoding='utf-8')
    _, selected, _ = module.load_and_validate(path, today)
    actual = {record['slug'] for record in selected}
    expected = {record['slug'] for record in published} - {target}
    assert actual == expected, f'Frontera de publicación incorrecta: {actual ^ expected}'
print('editoriales publication boundary: OK')
