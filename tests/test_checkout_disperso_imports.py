"""Un job con checkout disperso trae también los módulos propios que importan sus scripts (y los de estos).

2026-11-16: `gh_listas` se importó desde ci_intake_backup.py y ci_reflow_rotation.py, que corren en jobs que solo
descargan ese fichero: la carga y el reflow habrían fallado con ModuleNotFoundError antes de decidir nada.
"""
import ast
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def propios(script):
    """Módulos de scripts/ que importa `script`, transitivamente."""
    vistos, pendientes = set(), [script]
    while pendientes:
        actual = pendientes.pop()
        arbol = ast.parse((ROOT / actual).read_text(encoding='utf-8'))
        for nodo in ast.walk(arbol):
            nombres = [a.name for a in nodo.names] if isinstance(nodo, ast.Import) else \
                [nodo.module] if isinstance(nodo, ast.ImportFrom) and nodo.module and not nodo.level else []
            for nombre in nombres:
                ruta = f"scripts/{nombre.split('.')[0]}.py"
                if (ROOT / ruta).exists() and ruta not in vistos:
                    vistos.add(ruta)
                    pendientes.append(ruta)
    return vistos


class CheckoutDisperso(unittest.TestCase):
    def test_los_imports_propios_vienen_en_el_checkout(self):
        revisados = 0
        for wf in sorted((ROOT / '.github/workflows').glob('*.yml')):
            jobs = (yaml.safe_load(wf.read_text(encoding='utf-8')) or {}).get('jobs') or {}
            for nombre, job in jobs.items():
                for paso in job.get('steps') or []:
                    disperso = str((paso.get('with') or {}).get('sparse-checkout') or '')
                    rutas = {r.strip().lstrip('/') for r in disperso.splitlines() if r.strip()}
                    if not rutas or any(r == '*' or r.endswith('/') or '*' in r for r in rutas):
                        continue  # vacío o checkout amplio: trae scripts/ entero
                    for script in sorted(r for r in rutas if r.startswith('scripts/') and r.endswith('.py')):
                        revisados += 1
                        faltan = sorted(propios(script) - rutas)
                        self.assertEqual(faltan, [], f'{wf.name}:{nombre}: {script} importa {faltan}')
        self.assertGreater(revisados, 0)


if __name__ == '__main__':
    unittest.main()
