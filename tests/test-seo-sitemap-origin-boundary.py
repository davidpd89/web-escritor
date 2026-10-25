#!/usr/bin/env python3
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_origin_test', ROOT / 'scripts/build-sitemap.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    page = root / 'index.html'
    page.write_text('<html></html>', encoding='utf-8')

    valid = [
        'https://davidportodiaz.com/',
        'https://davidportodiaz.com/editoriales/',
    ]
    invalid = [
        'https://davidportodiaz.com.evil.invalid/editoriales/',
        'https://davidportodiaz.com@evil.invalid/editoriales/',
        'https://davidportodiaz.com.attacker.test/',
        'https://evil.invalid/editoriales/',
    ]

    for url in valid:
        actual = mod.normalize_canonical(url, root, page)
        assert actual == url, f'Canonical legítimo rechazado: {url} -> {actual}'

    for url in invalid:
        actual = mod.normalize_canonical(url, root, page)
        assert actual is None, f'Canonical de origen externo aceptado: {url} -> {actual}'

print('OK: el sitemap rechaza hostnames externos y ataques de prefijo')
