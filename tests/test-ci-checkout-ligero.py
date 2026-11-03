"""Cada actions/checkout baja el árbol sin assets/no usadas/ y sin blobs que no va a usar.

Esa carpeta son ~400 MB de originales que no se publican (build-public-dist y .assetsignore ya la
excluyen). Con ella el checkout tardaba de 2 a 18 minutos y algunos se colgaban hasta el límite del job.
Un checkout con su propio `sparse-checkout` (solo una carpeta) ya baja menos y queda fuera.
Lee el texto (el gate no tiene PyYAML): el paso son las líneas tras `uses:` más sangradas que su `- `.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPARSE = ['/*', '!/assets/no usadas/']

errors = []
count = 0
for path in sorted((ROOT / '.github' / 'workflows').glob('*.yml')):
    lines = path.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        m = re.match(r'^(\s*)(- )?uses:\s*actions/checkout@', line)
        if not m:
            continue
        key = len(m[1]) + (2 if m[2] else 0)
        step = []
        for nxt in lines[i + 1:]:
            if nxt.strip() and (len(nxt) - len(nxt.lstrip()) < key or nxt.lstrip().startswith('- ') and len(nxt) - len(nxt.lstrip()) == key):
                break
            step.append(nxt)
        if not m[2]:
            # `uses:` no abre el paso: las claves anteriores del mismo `- ` también cuentan.
            for prev in reversed(lines[:i]):
                step.insert(0, prev)
                if prev.lstrip().startswith('- '):
                    break
        opts = {}
        for k, raw in enumerate(step):
            kv = re.match(r'^\s*(filter|sparse-checkout-cone-mode|sparse-checkout):\s*(.*)$', raw)
            if not kv:
                continue
            if kv[1] == 'sparse-checkout' and kv[2] == '|':
                indent = len(raw) - len(raw.lstrip())
                body = []
                for b in step[k + 1:]:
                    if b.strip() and len(b) - len(b.lstrip()) <= indent:
                        break
                    if b.strip():
                        body.append(b.strip())
                opts[kv[1]] = body
            else:
                opts[kv[1]] = kv[2].strip()
        if 'sparse-checkout' in opts and opts['sparse-checkout'] != SPARSE:
            continue
        count += 1
        where = f'{path.name}:{i + 1}'
        if opts.get('sparse-checkout') != SPARSE or opts.get('sparse-checkout-cone-mode') != 'false':
            errors.append(f'{where}: falta sparse-checkout "/*" + "!/assets/no usadas/" con sparse-checkout-cone-mode: false')
        if opts.get('filter') != 'blob:none':
            errors.append(f'{where}: falta filter: blob:none')

if errors or not count:
    print('\n'.join(errors) or 'no se encontró ningún actions/checkout')
    sys.exit(1)
print(f'PASS checkout ligero en {count} pasos actions/checkout')
