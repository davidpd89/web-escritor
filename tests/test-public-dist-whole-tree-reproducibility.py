#!/usr/bin/env python3
import hashlib
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('public_dist_repro_qa', ROOT / 'scripts/build-public-dist.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob('*')) if p.is_file()}

critical = ['index.html', 'script.js', 'styles.css', 'service-worker.js', '404.html', 'offline.html', 'privacidad.html', 'eventos.html', 'ferias.html', 'premios.html', 'asistente/index.html']
originals = {name: digest(ROOT / name) for name in critical}
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / 'public'
    mod.build(out, ROOT)
    first = snapshot(out)
    assert set(critical) <= set(first), 'Faltan recursos públicos esenciales'
    assert len(first) > len(critical)
    mod.build(out, ROOT)
    second = snapshot(out)
    assert first == second, 'El segundo build cambió el árbol público'
    assert mod.check_contents(out, ROOT) == 0
assert originals == {name: digest(ROOT / name) for name in critical}, 'El builder mutó archivos fuente'
print(f'PASS: {len(first)} archivos públicos reproducibles')
