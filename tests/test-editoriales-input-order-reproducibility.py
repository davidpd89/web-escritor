#!/usr/bin/env python3
import copy
import hashlib
import importlib.util
import json
import random
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('editoriales_perm_qa', ROOT / 'scripts/build-editoriales.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
source = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
published = [r for r in source['publishers'] if r.get('publish') is True]
assert published
today = max(date.fromisoformat(r['verified_at']) for r in published)

def snapshot(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}

results = []
for seed in (0, 3, 8):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = copy.deepcopy(source)
        random.Random(seed).shuffle(data['publishers'])
        path = root / 'editoriales.json'
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        target = root / 'output'
        count, warnings = mod.build(path, target, today, False)
        assert count == len(published)
        results.append(snapshot(target))
assert all(result == results[0] for result in results[1:]), 'Deriva según el orden de entrada'
assert 'editoriales-sitemap.xml' in results[0]
print(f'PASS: {len(results)} permutaciones y {len(results[0])} artefactos')
