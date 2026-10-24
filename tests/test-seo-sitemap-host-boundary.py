from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_under_test', ROOT / 'scripts/build-sitemap.py')
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

page = ROOT / 'libros/index.html'
valid = [
    'https://davidportodiaz.com/libros/',
    '/libros/',
]
invalid = [
    'https://davidportodiaz.com.evil.invalid/libros/',
    'https://davidportodiaz.com.attacker.example/',
    'https://sub.davidportodiaz.com/libros/',
    'https://otro-dominio.example/libros/',
    'https://davidportodiaz.com@evil.invalid/libros/',
]

for value in valid:
    actual = mod.normalize_canonical(value, ROOT, page)
    assert actual == 'https://davidportodiaz.com/libros/', (value, actual)

for value in invalid:
    actual = mod.normalize_canonical(value, ROOT, page)
    assert actual is None, f'Canonical externo aceptado: {value} -> {actual}'

print('PASS sitemap exact-host boundary')
