#!/usr/bin/env python3
"""Toda lectura de un fichero con `git show` desde Node fija `maxBuffer`.

El tope por defecto de execFileSync/spawnSync es 1 MB: una página grande de la base (p. ej. antes del sprite de
iconos, #1432) tumbaba findability-qa con `spawnSync git ENOBUFS`. El tamaño de un fichero no está acotado, así
que la llamada debe declarar su tope en lugar de depender del de Node.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALL = re.compile(r"(?:execFileSync|spawnSync)\(\s*'git'\s*,\s*\[\s*'show'[^;]*", re.S)

fuera = []
ficheros = subprocess.run(['git', 'ls-files', '-z', '*.mjs', '*.js', '*.cjs'], cwd=ROOT, capture_output=True,
                          check=True).stdout.decode('utf-8').split('\0')
for rel in filter(None, ficheros):
    texto = (ROOT / rel).read_text(encoding='utf-8', errors='ignore')
    for m in CALL.finditer(texto):
        if 'maxBuffer' not in m.group(0):
            fuera.append(f"{rel}:{texto.count(chr(10), 0, m.start()) + 1}")
if fuera:
    print('FAIL: git show sin maxBuffer (ENOBUFS con ficheros de más de 1 MB):')
    print('\n'.join('  ' + f for f in fuera))
    sys.exit(1)
print('tests/test-git-show-maxbuffer: OK')
