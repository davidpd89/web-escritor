"""Cada actions/checkout baja el árbol sin assets/no usadas/ y sin blobs que no va a usar.

Esa carpeta son ~400 MB de originales que no se publican (build-public-dist y .assetsignore ya la
excluyen). Con ella el checkout tardaba de 2 a 18 minutos y algunos se colgaban hasta el límite del job.
Un checkout con su propio `sparse-checkout` (solo una carpeta) ya baja menos y queda fuera.
"""
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPARSE = '/*\n!/assets/no usadas/\n'

errors = []
count = 0
for path in sorted((ROOT / '.github/workflows').glob('*.yml')):
    flow = yaml.safe_load(path.read_text(encoding='utf-8'))
    for job_name, job in (flow.get('jobs') or {}).items():
        for step in job.get('steps') or []:
            if not str(step.get('uses', '')).startswith('actions/checkout'):
                continue
            opts = step.get('with') or {}
            if 'sparse-checkout' in opts and opts['sparse-checkout'] != SPARSE:
                continue
            count += 1
            where = f'{path.name} ({job_name})'
            if opts.get('sparse-checkout') != SPARSE or opts.get('sparse-checkout-cone-mode') is not False:
                errors.append(f'{where}: falta sparse-checkout "/*" + "!/assets/no usadas/" con sparse-checkout-cone-mode: false')
            if opts.get('filter') != 'blob:none':
                errors.append(f'{where}: falta filter: blob:none')

if errors:
    print('\n'.join(errors))
    sys.exit(1)
print(f'PASS checkout ligero en {count} pasos actions/checkout')
