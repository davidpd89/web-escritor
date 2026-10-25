#!/usr/bin/env python3
"""Controles visualmente ocultos (.sr-only) fuera del orden de Tab en HTML versionados.

Un boton .sr-only (1x1 px) que recibe el foco deja al usuario de teclado en un control invisible: el Post-deploy deep audit lo
detecto en /herramientas/json-ld-escritores/ (2026-10-25). Los submit ocultos existen para el envio implicito con Enter, que
sigue funcionando con tabindex="-1". Excepcion: <input type="file"> oculto con <label> visible (patron estandar de subida).
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = ('tests/', 'qa/', 'docs/', 'lab/')
NAMES = subprocess.check_output(
    ['git', '-c', 'core.quotepath=false', 'ls-files', '*.html', 'scripts/*.py'],
    cwd=ROOT, text=True
).splitlines()
CONTROL = re.compile(r'<(button|a|select|textarea|input)\b([^>]*)>', re.I)
errors = []
checked = 0

for rel in NAMES:
    if rel.startswith(EXCLUDED) or rel == 'video-ios-test/index.html':
        continue
    text = (ROOT / rel).read_text(encoding='utf-8', errors='replace')
    checked += 1
    for tag, attrs in CONTROL.findall(text):
        clases = re.search(r'class=["\']([^"\']*)["\']', attrs)
        if not clases or 'sr-only' not in clases.group(1).split():
            continue
        if tag.lower() == 'a' and 'href' not in attrs:
            continue
        if tag.lower() == 'input' and re.search(r'type=["\'](hidden|file)["\']', attrs, re.I):
            continue
        if re.search(r'tabindex=["\']-1["\']', attrs):
            continue
        errors.append(f'{rel}: <{tag}{attrs[:80]}> oculto con .sr-only pero alcanzable con Tab')

assert checked > 0, 'No se han encontrado ficheros comprobables'
for error in errors:
    print('FAIL', error)
print(f'sr-only-controls: {checked} ficheros, {len(errors)} fallos')
raise SystemExit(bool(errors))
