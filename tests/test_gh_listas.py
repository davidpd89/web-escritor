"""Fable R4-12 (F9): ninguna lista de GitHub se corta en silencio.

`gh ... list --limit N` y `per_page=N` devuelven como mucho N sin avisar. La guarda recorre scripts/*.py por AST y
exige que toda lista pase por scripts/gh_listas.py, que pagina, falla al llegar al tope o declara una ventana.
"""
import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import gh_listas  # noqa: E402

AYUDANTES = {'lista', 'ultimas', 'rest_todas', 'rest_ultimas'}
LISTABLES = {'run', 'pr', 'issue', 'release', 'workflow', 'label', 'repo', 'secret', 'variable', 'cache'}


def _nombre(func):
    return func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', '')


def _textos(nodo):
    """Literales de texto de un nodo (también las partes fijas de un f-string)."""
    for x in ast.walk(nodo):
        if isinstance(x, ast.Constant) and isinstance(x.value, str):
            yield x.value


def infracciones(fuente, nombre='x.py'):
    arbol = ast.parse(fuente)
    padres = {hijo: padre for padre in ast.walk(arbol) for hijo in ast.iter_child_nodes(padre)}

    def llamada(nodo):
        while nodo in padres and not isinstance(nodo, ast.Call):
            nodo = padres[nodo]
        return nodo if isinstance(nodo, ast.Call) else None

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            if nodo.value in ('--limit', '-L'):
                yield f'{nombre}:{nodo.lineno} --limit'
            elif 'per_page=' in nodo.value:
                c = llamada(nodo)
                if c is None or '--paginate' not in list(_textos(c)):
                    yield f'{nombre}:{nodo.lineno} per_page sin --paginate'
        elif isinstance(nodo, ast.Call) and _nombre(nodo.func) not in AYUDANTES:
            fijos = [a.value for a in nodo.args if isinstance(a, ast.Constant)]
            for x in nodo.args:
                if isinstance(x, (ast.List, ast.Tuple)):
                    fijos += [e.value for e in x.elts if isinstance(e, ast.Constant)]
            if any(a in LISTABLES and b == 'list' for a, b in zip(fijos, fijos[1:])):
                yield f'{nombre}:{nodo.lineno} lista de gh sin gh_listas'


class GuardaTest(unittest.TestCase):
    def test_ningun_script_corta_una_lista_en_silencio(self):
        fuera = [i for f in sorted((ROOT / 'scripts').glob('*.py')) if f.name != 'gh_listas.py'
                 for i in infracciones(f.read_text(encoding='utf-8'), f.name)]
        self.assertEqual(fuera, [], 'usar gh_listas.lista/ultimas/rest_todas/rest_ultimas')

    def test_la_guarda_ve_cada_forma(self):
        malos = ["gh('run', 'list', '--limit', '20')",
                 "gh('pr', 'list', '--state', 'open')",                 # sin --limit: gh corta en 30
                 "subprocess.run(['gh', 'issue', 'list', '--json', 'n'])",
                 "api(f'/repos/{r}/runs?per_page=50')",
                 "gh('api', f'repos/{r}/pulls/1/files?per_page=100')"]
        for malo in malos:
            with self.subTest(malo=malo):
                self.assertTrue(list(infracciones(malo)))
        buenos = ["gh_listas.lista(gh, 'pr', 'list', '--state', 'open')",
                  "ultimas(gh, 'run', 'list', n=1)",
                  "gh('api', '--paginate', '--slurp', f'repos/{r}/pulls/1/files?per_page=100')",
                  "gh('pr', 'view', '1')"]
        for bueno in buenos:
            with self.subTest(bueno=bueno):
                self.assertEqual(list(infracciones(bueno)), [])


class AyudantesTest(unittest.TestCase):
    def test_lista_completa_o_truncada(self):
        def gh(*args):
            n = int(args[args.index('--limit') + 1])
            return json.dumps(list(range(min(n, 7))))
        self.assertEqual(len(gh_listas.lista(gh, 'pr', 'list', tope=8)), 7)
        with self.assertRaises(gh_listas.Truncada):
            gh_listas.lista(gh, 'pr', 'list', tope=7)
        self.assertEqual(gh_listas.ultimas(gh, 'run', 'list', n=3), [0, 1, 2])

    def test_rest_todas_sigue_las_paginas(self):
        pedidas = []

        def api(ruta):
            pedidas.append(ruta)
            pagina = int(ruta.rsplit('page=', 1)[1])
            return {'jobs': list(range(100)) if pagina < 3 else [1, 2]}
        self.assertEqual(len(gh_listas.rest_todas(api, '/r/jobs?filter=all', 'jobs')), 202)
        self.assertEqual(pedidas[0], '/r/jobs?filter=all&per_page=100&page=1')
        with self.assertRaises(gh_listas.Truncada):
            gh_listas.rest_todas(lambda r: {'jobs': list(range(100))}, '/r', 'jobs', max_paginas=2)

    def test_rest_todas_no_repite_lo_que_la_lista_viva_empuja(self):
        # Entre la página 1 y la 2 llega un elemento nuevo: el último de la 1 reaparece al principio de la 2.
        paginas = {1: [{'id': i} for i in range(100, 0, -1)], 2: [{'id': 1}, {'id': 0}]}
        todas = gh_listas.rest_todas(lambda r: paginas[int(r.rsplit('page=', 1)[1])], '/r')
        self.assertEqual([x['id'] for x in todas], list(range(100, -1, -1)))


class ExistingPrTest(unittest.TestCase):
    """R5-11 (hallazgo 30): si no se sabe si la PR ya existe, no se crea otra."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location('publish_radar_refresh', ROOT / 'scripts' / 'publish-radar-refresh.py')
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def _con_gh(self, stdout=None, error=None):
        import subprocess
        from unittest import mock

        def run(cmd, **kw):
            if error:
                raise error
            n = int(cmd[cmd.index('--limit') + 1])
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(stdout(n)), stderr='')
        return mock.patch.object(self.mod.subprocess, 'run', run)

    def test_mas_resultados_que_el_tope_no_es_no_hay(self):
        args = ('pr', 'create', '--head', 'rama')
        with self._con_gh(lambda n: [{'url': f'u{i}'} for i in range(n)]):
            with self.assertRaises(gh_listas.Truncada):
                self.mod._existing_pr(args)

    def test_si_gh_falla_no_es_no_hay(self):
        import subprocess
        with self._con_gh(error=subprocess.CalledProcessError(1, 'gh')):
            with self.assertRaises(subprocess.CalledProcessError):
                self.mod._existing_pr(('pr', 'create', '--head', 'rama'))

    def test_encuentra_la_que_llego_a_crearse(self):
        with self._con_gh(lambda n: [{'url': 'https://x/pull/1'}]):
            self.assertEqual(self.mod._existing_pr(('pr', 'create', '--head', 'rama')), 'https://x/pull/1')


if __name__ == '__main__':
    unittest.main()
