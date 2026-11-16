"""Un job con checkout disperso trae también los módulos propios que importan sus scripts (y los de estos).

2026-11-16: `gh_listas` se importó desde ci_intake_backup.py y ci_reflow_rotation.py, que corren en jobs que solo
descargan ese fichero: la carga y el reflow habrían fallado con ModuleNotFoundError antes de decidir nada.
"""
import ast
import fnmatch
import functools
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


@functools.cache
def directos(script):
    """Módulos de scripts/ que `script` importa directamente (cada fichero se analiza una sola vez)."""
    salida = set()
    for nodo in ast.walk(ast.parse((ROOT / script).read_text(encoding='utf-8'))):
        nombres = [a.name for a in nodo.names] if isinstance(nodo, ast.Import) else \
            [nodo.module] if isinstance(nodo, ast.ImportFrom) and nodo.module and not nodo.level else []
        salida.update(r for r in (f"scripts/{n.split('.')[0]}.py" for n in nombres) if (ROOT / r).exists())
    return frozenset(salida)


@functools.cache
def propios(script):
    """Módulos de scripts/ que importa `script`, transitivamente."""
    vistos, pendientes = set(), [script]
    while pendientes:
        for ruta in directos(pendientes.pop()) - vistos:
            vistos.add(ruta)
            pendientes.append(ruta)
    return frozenset(vistos)


def cubre(rutas, fichero):
    """¿Trae el checkout disperso (modo no-cono) `fichero`? Solo cuenta una ruta que lo nombre o un prefijo/comodín
    que lo abarque; `tests/` o `docs/*` no traen nada de scripts/. Las exclusiones (`!…`) quitan."""
    dentro = False
    for r in rutas:
        neg, patron = r.startswith('!'), r.lstrip('!').lstrip('/')
        if patron == fichero or (patron.endswith('/') and fichero.startswith(patron)) or (
                any(c in patron for c in '*?[') and fnmatch.fnmatchcase(fichero, patron)) or (
                patron.endswith('/*') and fichero.startswith(patron[:-1])):
            dentro = not neg
    return dentro


TODOS = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / 'scripts').glob('*.py'))


def faltan(disperso):
    """Módulos propios que importan los scripts del checkout (nombrados o traídos por un directorio o comodín) y
    que el checkout no trae."""
    rutas = [r.strip() for r in disperso.splitlines() if r.strip()]
    scripts = [s for s in TODOS if cubre(rutas, s)]
    return sorted({m for s in scripts for m in propios(s) if not cubre(rutas, m)}), len(scripts)


class CheckoutDisperso(unittest.TestCase):
    def test_los_imports_propios_vienen_en_el_checkout(self):
        revisados = 0
        for wf in sorted((ROOT / '.github/workflows').glob('*.yml')):
            jobs = (yaml.safe_load(wf.read_text(encoding='utf-8')) or {}).get('jobs') or {}
            for nombre, job in jobs.items():
                for paso in job.get('steps') or []:
                    disperso = str((paso.get('with') or {}).get('sparse-checkout') or '')
                    perdidos, n = faltan(disperso)
                    revisados += n
                    self.assertEqual(perdidos, [], f'{wf.name}:{nombre}: el checkout no trae {perdidos}')
        self.assertGreater(revisados, 0)

    def test_una_ruta_amplia_ajena_a_scripts_no_tapa_un_import_perdido(self):
        def caso(*rutas):
            return faltan('\n'.join(rutas))[0]
        self.assertEqual(caso('scripts/ci_intake_backup.py', 'tests/'), ['scripts/gh_listas.py'])
        self.assertEqual(caso('scripts/ci_intake_backup.py', 'docs/*'), ['scripts/gh_listas.py'])
        self.assertEqual(caso('scripts/ci_intake_backup.py', 'scripts/gh_listas.py'), [])
        self.assertEqual(caso('scripts/ci_intake_backup.py', 'scripts/'), [])
        self.assertEqual(caso('scripts/ci_intake_backup.py', 'scripts/*'), [])
        self.assertEqual(caso('/*', '!/assets/no usadas/'), [])
        # Un directorio trae ci_intake_backup.py aunque no se nombre; una exclusión con ? o [] sí quita gh_listas.
        self.assertEqual(caso('scripts/', '!/scripts/gh_listas.py'), ['scripts/gh_listas.py'])
        self.assertEqual(caso('scripts/ci_intake_backup.py', 'scripts/gh_listas.py', '!/scripts/gh_lista?.py'),
                         ['scripts/gh_listas.py'])
        self.assertEqual(caso('scripts/ci_intake_backup.py', 'scripts/gh_listas.py', '!/scripts/gh_[l]istas.py'),
                         ['scripts/gh_listas.py'])


if __name__ == '__main__':
    unittest.main()
