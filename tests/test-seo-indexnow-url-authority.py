#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('indexnow_authority_test', ROOT / 'scripts/indexnow.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

valid = [
    'https://davidportodiaz.com/',
    'https://davidportodiaz.com/cuaderno/',
    'https://davidportodiaz.com/editoriales/adel-editores/',
]
invalid = [
    'https://usuario@davidportodiaz.com/cuaderno/',
    'https://usuario:clave@davidportodiaz.com/cuaderno/',
    'https://davidportodiaz.com:8443/cuaderno/',
    'https://davidportodiaz.com:8080/',
    'https://davidportodiaz.com.evil.invalid/',
]

for url in valid:
    mod.validate_url(url)

for url in invalid:
    try:
        mod.validate_url(url)
    except ValueError:
        continue
    raise AssertionError(f'IndexNow acepta una autoridad URL no autorizada: {url}')

print('OK: validación estricta de la autoridad en IndexNow')
