#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checklist = (ROOT / 'publicar-web/index.html').read_text(encoding='utf-8')
hub = (ROOT / 'herramientas/index.html').read_text(encoding='utf-8')

shared = ('v1-fonts.css', 'v1-base.css')
errors = []
for asset in shared:
    if asset not in hub:
        errors.append(f'El referente visual no utiliza {asset}')
    if asset not in checklist:
        errors.append(f'El checklist carece de {asset}')

styles = re.findall(r'<link\b[^>]*rel=["\']stylesheet["\'][^>]*>', checklist, re.I)
if not styles:
    errors.append('Checklist sin hoja de estilos compartida')

for asset in shared:
    assert (ROOT / 'assets' / asset).is_file(), asset

assert not errors, '\n'.join(errors)
print('PASS publicar-web: tipografía y estilos compartidos')
