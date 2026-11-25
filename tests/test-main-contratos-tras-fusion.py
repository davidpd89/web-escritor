"""main-contratos.yml corre tras cada fusión los mismos contratos que la puerta y la autorreparación lo vigila.

El 24/11 dos PR verdes por separado (#1564 y #1395) dejaron main en rojo y nadie lo vio hasta que las cargas de la
noche cayeron en la puerta. Este contrato impide que la comprobación de main se desvíe de la puerta o deje de vigilarse.
"""
import ast
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parents[1]
flujo = (RAIZ / '.github/workflows/main-contratos.yml').read_text(encoding='utf-8')
puerta = (RAIZ / '.github/workflows/required-merge-gate.yml').read_text(encoding='utf-8')

for modo in ('guion', 'subrayado'):
    orden = f'bash scripts/run-python-contracts.sh {modo}'
    assert orden in puerta, f'la puerta ya no usa {orden!r}: main-contratos.yml debe seguirla'
    assert orden in flujo, f'main-contratos.yml no corre {orden!r} como la puerta'

assert re.search(r'push:\s*\n\s*branches:\s*\[main\]', flujo), 'main-contratos.yml debe dispararse con push a main'
assert 'workflow_dispatch' in flujo, 'la autorreparación relanza con workflow_dispatch'
for ruta in ('scripts/**', 'tests/**', '.github/workflows/**'):
    assert f"'{ruta}'" in flujo, f'main-contratos.yml no se dispara con cambios en {ruta}'

arbol = ast.parse((RAIZ / 'scripts/night-autorepair.py').read_text(encoding='utf-8'))
vigilados = next(ast.literal_eval(n.value) for n in arbol.body
                 if isinstance(n, ast.Assign) and any(getattr(t, 'id', '') == 'VIGILADOS' for t in n.targets))
assert 'main-contratos.yml' in vigilados, 'night-autorepair.py no vigila main-contratos.yml'
print('main-contratos tras fusión: OK')
