#!/usr/bin/env python3
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build-radar-opportunities.py'
source = json.loads((ROOT / 'data/radar-opportunities.json').read_text(encoding='utf-8'))
seed = next(item for item in source['items'] if item.get('published') is True)

def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    data = root / 'data.json'
    out = root / 'out'
    payload = {'schema_version': 1, 'items': [seed], 'watchlist': []}
    data.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    command = [sys.executable, str(SCRIPT), '--data', str(data), '--out', str(out), '--today', '2026-10-24']
    first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    baseline = snapshot(out)
    assert {'index.html', 'opportunities.json', 'deadlines.ics'} <= set(baseline)
    checked = subprocess.run(command + ['--check'], cwd=ROOT, capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
    assert snapshot(out) == baseline
    bad = copy.deepcopy(payload)
    bad['items'][0]['prioridad_privada'] = 'confidencial'
    data.write_text(json.dumps(bad, ensure_ascii=False), encoding='utf-8')
    rejected = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert rejected.returncode != 0, 'Datos privados aceptados'
    assert snapshot(out) == baseline, 'El fallo alteró artefactos válidos'
print('PASS: validación sin escrituras y generación atómica')
