"""main-contratos.yml corre tras cada fusión los mismos contratos que la puerta y la autorreparación lo vigila.

El 24/11 dos PR verdes por separado (#1564 y #1395) dejaron main en rojo y nadie lo vio hasta que las cargas de la
noche cayeron en la puerta. Este contrato impide que la comprobación de main se desvíe de la puerta o deje de vigilarse.
"""
import ast
import os
import pathlib
import re
import tempfile

# Solo lee night-autorepair.py con ast (no lo carga); igualmente aislado, como pide su contrato de estado local.
os.environ['AUTOREPAIR_ESTADO_DIR'] = tempfile.mkdtemp()

RAIZ = pathlib.Path(__file__).resolve().parents[1]
flujo = (RAIZ / '.github/workflows/main-contratos.yml').read_text(encoding='utf-8')
puerta = (RAIZ / '.github/workflows/required-merge-gate.yml').read_text(encoding='utf-8')

# Toda orden de contratos de la puerta corre también en main (R5-02, 25/11: los tests/*.mjs solo iban en la puerta).
ordenes = set(re.findall(r'bash scripts/run-[\w-]+-contracts\.sh(?: \w+)?', puerta))
assert {'bash scripts/run-python-contracts.sh guion', 'bash scripts/run-python-contracts.sh subrayado',
        'bash scripts/run-node-contracts.sh'} <= ordenes, f'la puerta ya no usa los scripts de contratos: {ordenes}'
for orden in sorted(ordenes):
    assert orden in flujo, f'main-contratos.yml no corre {orden!r} como la puerta'
assert 'for f in tests/*.mjs' not in puerta, 'los contratos Node de la puerta van por scripts/run-node-contracts.sh'

assert re.search(r'push:\s*\n\s*branches:\s*\[main\]', flujo), 'main-contratos.yml debe dispararse con push a main'
assert 'workflow_dispatch' in flujo, 'la autorreparación relanza con workflow_dispatch'
for ruta in ('scripts/**', 'tests/**', '.github/workflows/**'):
    assert f"'{ruta}'" in flujo, f'main-contratos.yml no se dispara con cambios en {ruta}'

arbol = ast.parse((RAIZ / 'scripts/night-autorepair.py').read_text(encoding='utf-8'))
vigilados = next(ast.literal_eval(n.value) for n in arbol.body
                 if isinstance(n, ast.Assign) and any(getattr(t, 'id', '') == 'VIGILADOS' for t in n.targets))
assert 'main-contratos.yml' in vigilados, 'night-autorepair.py no vigila main-contratos.yml'
print('main-contratos tras fusión: OK')
