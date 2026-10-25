#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_sitemap', ROOT / 'scripts/build-sitemap.py')
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = ROOT / 'index.html'
valid = [
    'https://davidportodiaz.com/',
    'https://davidportodiaz.com/cuaderno/',
]
invalid = [
    'https://davidportodiaz.com.evil.example/cuaderno/',
    'https://davidportodiaz.com@evil.example/cuaderno/',
    'https://davidportodiaz.com:444/cuaderno/',
    'https://davidportodiaz.com.evil.example/',
    'https://evil.example/davidportodiaz.com/',
    'https://davidportodiaz.com:443@evil.example/',
]

for url in valid:
    result = module.normalize_canonical(url, ROOT, source)
    assert result == url, f'Canonical válido alterado: {url!r} -> {result!r}'

for url in invalid:
    result = module.normalize_canonical(url, ROOT, source)
    assert result is None, f'Canonical externo aceptado: {url!r} -> {result!r}'

print('PASS canonical origin boundary')
