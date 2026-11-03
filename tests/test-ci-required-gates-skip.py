"""Checks obligatorios del ruleset: siempre dan resultado y se saltan solos si la PR no les afecta.

Un `paths:` en `on.pull_request` deja el check en «Expected» para siempre en una PR que no toca
esas rutas y bloquea el merge. Por eso el trigger no filtra y un paso decide si hay que medir.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATED = ['pa11y-baseline.yml', 'lighthouse-ci.yml']
ALWAYS = GATED + ['sitewide-reflow-qa.yml', 'visual-regression-qa.yml', 'public-artifact-contract.yml', 'required-merge-gate.yml']

errors = []
for name in ALWAYS:
    text = (ROOT / '.github/workflows' / name).read_text(encoding='utf-8')
    block = re.search(r'^  pull_request:\n((?:    .*\n|\s*\n)*)', text, re.M)
    if not block:
        errors.append(f'{name}: sin trigger pull_request')
    elif re.search(r'^\s+paths(-ignore)?:', block.group(1), re.M):
        errors.append(f'{name}: pull_request filtra por rutas y el check obligatorio quedaría en Expected')
for name in GATED:
    text = (ROOT / '.github/workflows' / name).read_text(encoding='utf-8')
    if 'id: changes' not in text or "steps.changes.outputs.relevant == 'true'" not in text:
        errors.append(f'{name}: falta el paso que salta la medición en PR sin cambios relevantes')
    if 'fetch-depth: 0' not in text:
        errors.append(f'{name}: el diff con la base necesita fetch-depth: 0')

if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('PASS checks obligatorios: sin filtro de rutas y con salto por cambios relevantes')
