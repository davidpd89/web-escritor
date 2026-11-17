#!/usr/bin/env python3
"""R4-8: la política del portero solo deja fusionar sola una PR del reparador de forma inofensiva.

Escenarios sintéticos sobre `revisar()`: no ejecuta git ni el parche.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('politica', ROOT / 'scripts/reparador_politica.py')
politica = importlib.util.module_from_spec(spec)
spec.loader.exec_module(politica)
revisar = politica.revisar

BASE = 'import json\n\ndef f(x):\n    return json.dumps(x)\n'


def py(despues, antes=BASE, path='scripts/reading_algo.py', lineas=10):
    return revisar({path: (antes, despues)}, lineas)


# Inocuo: un .py que solo cambia lógica y un .md → se fusiona solo.
assert py(BASE + '\ndef g(y):\n    return f(y) or {}\n') == []
assert revisar({'docs/nota.md': ('a', 'b'), 'data/x.json': (None, '{}')}, 5) == []
# Borrar un módulo Python no añade capacidades.
assert revisar({'scripts/viejo.py': (BASE, None)}, 4) == []

# Rutas protegidas, aunque el contenido sea inocuo.
for path in ('.github/workflows/x.yml', 'AGENTS.md', 'CLAUDE.md', '.claude/settings.json', 'package.json',
             'scripts/requirements.txt', 'scripts/requirements-reading-audio.txt', 'scripts/reparador_politica.py',
             'tests/test-reparador-politica.py', 'sub/package-lock.json'):
    motivos = revisar({path: ('a', 'b')}, 2)
    assert motivos == [f'{path}: ruta protegida'], (path, motivos)

# Tipos que no se revisan sin ejecutarlos van a David.
for path in ('qa/x.mjs', 'scripts/x.sh', 'config/x.yml', 'index.html', 'Makefile'):
    motivos = revisar({path: ('a', 'b')}, 2)
    assert len(motivos) == 1 and 'no revisable' in motivos[0], (path, motivos)

# Capacidades nuevas, cada forma por separado.
peligrosos = {
    'import subprocess': 'import subprocess\n',
    'import urllib': 'from urllib.request import urlopen\n',
    'import socket': 'import socket as s\n',
    'os.environ': 'import os\nX = os.environ["T"]\n',
    'os.getenv': 'from os import getenv\n',
    'os.system': 'import os as o\no.system("x")\n',
    'eval': 'eval("1")\n',
    'exec': 'exec("1")\n',
    '__import__': '__import__("os")\n',
    'builtins.exec': 'import builtins\nbuiltins.exec("1")\n',
    'getattr dinámico': 'import os\nn = "sys" + "tem"\ngetattr(os, n)("x")\n',
    'sys.modules': 'import sys\nsys.modules["os"]\n',
}
for clave, codigo in peligrosos.items():
    motivos = py(BASE + codigo)
    assert len(motivos) == 1 and clave in motivos[0], (clave, motivos)

# getattr con nombre literal sí se puede leer: no es motivo.
assert py(BASE + 'getattr(json, "dumps")\n') == []

# Lo que ya estaba no cuenta; un uso más del mismo sí.
CON_ENV = BASE + 'import os\nA = os.environ.get("A")\n'
assert py(CON_ENV + 'B = 2\n', antes=CON_ENV) == []
motivos = py(CON_ENV + 'B = os.environ.get("B")\n', antes=CON_ENV)
assert len(motivos) == 1 and 'os.environ' in motivos[0], motivos

# Fichero nuevo con red: motivo; sintaxis rota: motivo (no se puede revisar).
assert py('import requests\n', antes=None) == ['scripts/reading_algo.py: añade import requests']
assert py('def (:\n') == ['scripts/reading_algo.py: no se puede analizar']

# Tope de líneas.
motivos = py(BASE, lineas=politica.MAX_LINEAS + 1)
assert len(motivos) == 1 and 'tope' in motivos[0], motivos
assert py(BASE + 'Y = 1\n', lineas=politica.MAX_LINEAS) == []

# Varios motivos a la vez se listan todos.
motivos = revisar({'AGENTS.md': ('a', 'b'), 'scripts/a.py': (BASE, BASE + 'eval("1")\n')}, 500)
assert len(motivos) == 3, motivos

print('OK portero: solo parches inofensivos se fusionan solos')
