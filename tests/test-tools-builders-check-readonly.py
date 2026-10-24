#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

cases = [
    ('hub', 'scripts/build-tools-hub.py', 'data/tools-hub.json', False),
    ('writer', 'scripts/build-writer-tools.py', 'data/writer-tools.json', True),
]

with tempfile.TemporaryDirectory() as tmp:
    for name, script, data, named_output in cases:
        target = Path(tmp) / f'{name}.html'
        command = [PYTHON, str(ROOT / script), str(ROOT / data)]
        command += ['--output', str(target)] if named_output else [str(target)]
        def run(extra=()):
            return subprocess.run(command + list(extra), cwd=ROOT, capture_output=True, text=True)
        created = run()
        assert created.returncode == 0, (name, created.stderr)
        original = target.read_bytes()
        assert len(original) > 500, name
        checked = run(['--check'])
        assert checked.returncode == 0, (name, checked.stderr)
        assert target.read_bytes() == original
        target.write_bytes(original + b'\n<!-- qa-corruption -->')
        corrupted = target.read_bytes()
        rejected = run(['--check'])
        assert rejected.returncode != 0, f'{name}: no detecta alteraciones'
        assert target.read_bytes() == corrupted, f'{name}: --check modificó la salida'
        repaired = run()
        assert repaired.returncode == 0, (name, repaired.stderr)
        assert target.read_bytes() == original, f'{name}: no se restauró el resultado'
print('PASS: --check parametrizado en ambos generadores')
