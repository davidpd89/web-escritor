import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import materializar_generados as mat  # noqa: E402


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class UnaSolaCadena(unittest.TestCase):
    def test_los_llamadores_usan_el_modulo(self):
        for file in ('rebase-regenerando.py', 'merge-main.py', 'refresh-reading-catalogue.py'):
            texto = (ROOT / 'scripts' / file).read_text(encoding='utf-8')
            self.assertIn('materializar.construir(ROOT', texto, file)
            self.assertNotIn("('build-pagefind-index.py',)", texto, f'{file} vuelve a copiar la cadena')

    def test_el_codigo_de_recomendaciones_no_es_generado(self):
        self.assertFalse(mat.generado('recomendaciones/reading-catalogue.js'))
        self.assertTrue(mat.generado('recomendaciones/libro/x/index.html'))
        self.assertTrue(mat.generado('data/content-registry.json'))
        # Todo lo versionado en carpetas generadas sale de un builder: ninguno queda fuera de la regeneración.
        versionado = subprocess.run(['git', 'ls-files', 'recomendaciones', 'editoriales', 'mapa-del-sitio', 'pagefind'],
                                    cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual([p for p in versionado if not mat.generado(p)], [])
        self.assertIs(_load('rr', 'rebase-regenerando.py').generado, mat.generado)

    def test_los_indexadores_van_despues_de_crear_rutas(self):
        nombres = [b[0] for b in mat.BUILDERS]
        for indexa in ('build-site-shell.py', 'build-pagefind-index.py'):
            self.assertGreater(nombres.index(indexa), nombres.index('build-page-order.py'))


ACCION = './.github/actions/materializar'


class AccionMaterializar(unittest.TestCase):
    def test_la_accion_usa_la_cadena_unica(self):
        texto = (ROOT / '.github/actions/materializar/action.yml').read_text(encoding='utf-8')
        self.assertIn('scripts/materializar_generados.py --asegurar', texto)
        self.assertIn('actions/cache/restore', texto)
        self.assertIn("steps.build.outputs.construido == 'true'", texto)

    def test_todo_workflow_que_lee_lo_generado_materializa_antes(self):
        """Paso 2/4: sirve el árbol (http.server) o construye la distribución (build-public-dist) → la acción va
        antes, en el mismo job. Un workflow nuevo sin ella falla aquí; `python scripts/adoptar_materializar.py` la pone."""
        import importlib.util
        spec = importlib.util.spec_from_file_location('adoptar', ROOT / 'scripts/adoptar_materializar.py')
        adoptar = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adoptar)
        self.assertEqual(adoptar.pendientes(ROOT), [])
        flujo = (ROOT / '.github/workflows/deploy-pages.yml').read_text(encoding='utf-8')
        self.assertLess(flujo.index(ACCION), flujo.index('build-public-dist.py --out .preview-dist'))
        self.assertIn('materializar_generados.py --asegurar', flujo.split('git worktree add')[1].split('build-public-dist')[0])

    def test_versionado_la_accion_no_guarda_cache(self):
        import os, sys, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp, 'out')
            subprocess.run([sys.executable, str(ROOT / 'scripts/materializar_generados.py'), '--asegurar'], cwd=ROOT,
                           check=True, env={**os.environ, 'GITHUB_OUTPUT': str(salida)}, capture_output=True)
            self.assertEqual(salida.read_text(encoding='utf-8').strip(), 'construido=false')

    def test_adoptar_inserta_antes_del_primer_lector_y_hereda_la_condicion(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('adoptar', ROOT / 'scripts/adoptar_materializar.py')
        adoptar = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adoptar)
        flujo = """on: push
jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
      - name: Servir
        if: steps.sel.outputs.run == 'true'
        run: python -m http.server 4173 &
  otro:
    runs-on: ubuntu-latest
    steps:
      - run: echo hola
"""
        nuevo = adoptar.adoptar(flujo)
        self.assertEqual(adoptar.adoptar(nuevo), nuevo)
        qa = nuevo.split('  otro:')[0]
        self.assertLess(qa.index('setup-python'), qa.index(ACCION))
        self.assertLess(qa.index(ACCION), qa.index('http.server'))
        self.assertIn("        if: steps.sel.outputs.run == 'true'\n        uses: " + ACCION, qa)
        self.assertNotIn(ACCION, nuevo.split('  otro:')[1])

    def test_la_clave_de_cache_son_las_fuentes(self):
        import re
        texto = (ROOT / '.github/actions/materializar/action.yml').read_text(encoding='utf-8')
        clave = re.search(r"hashFiles\((.*?)\) \}\}", texto).group(1)
        self.assertEqual(tuple(re.findall(r"'([^']+)'", clave)), mat.FUENTES)


class AsegurarAntesDeLaSuite(unittest.TestCase):
    """Paso 3: la suite lee lo generado del árbol; tras el corte se materializa una vez, no test a test."""

    def _repo(self, d, versionar_generado):
        root = Path(d)
        git = lambda *a: subprocess.run(['git', *a], cwd=root, check=True, capture_output=True)
        git('init', '-q')
        (root / 'data').mkdir()
        (root / 'data/reading-books.json').write_text('[]', encoding='utf-8')
        (root / 'assets').mkdir()
        if versionar_generado:
            (root / mat.TESTIGO).write_text('//', encoding='utf-8')
        git('add', '.')
        git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'x')
        return root, git

    def _asegurar(self, root, construidas):
        from unittest import mock
        def construir(r, antes_de_indexar=None):
            construidas.append(r)
            (r / mat.TESTIGO).write_text('//', encoding='utf-8')
        with mock.patch.object(mat, 'construir', construir):
            return mat.asegurar(root)

    def test_versionado_no_construye(self):
        with tempfile.TemporaryDirectory() as d:
            root, _ = self._repo(d, versionar_generado=True)
            construidas = []
            self.assertFalse(self._asegurar(root, construidas))
            self.assertEqual(construidas, [])

    def test_tras_el_corte_construye_solo_si_cambian_las_fuentes(self):
        with tempfile.TemporaryDirectory() as d:
            root, git = self._repo(d, versionar_generado=False)
            construidas = []
            self.assertTrue(self._asegurar(root, construidas))
            self.assertFalse(self._asegurar(root, construidas))     # mismas fuentes: nada
            (root / 'data/reading-books.json').write_text('[{}]', encoding='utf-8')
            self.assertTrue(self._asegurar(root, construidas))      # cambió un dato (aún sin commitear)
            (root / mat.TESTIGO).unlink()
            self.assertTrue(self._asegurar(root, construidas))      # falta lo generado: se rehace
            self.assertEqual(len(construidas), 3)


class RutasNuevas(unittest.TestCase):
    def test_una_ficha_nueva_la_ve_ls_files_antes_de_indexar(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            git = lambda *a: subprocess.run(['git', *a], cwd=root, check=True, capture_output=True, text=True).stdout
            git('init', '-q')
            (root / 'recomendaciones' / 'libro' / 'nuevo').mkdir(parents=True)
            (root / 'recomendaciones' / 'libro' / 'nuevo' / 'index.html').write_text('<p>x</p>', encoding='utf-8')
            (root / 'recomendaciones' / 'borrador.txt').write_text('x', encoding='utf-8')
            self.assertEqual(git('ls-files', '*.html'), '')
            nuevas = mat.registrar_rutas_nuevas(root)
            self.assertEqual(nuevas, ['recomendaciones/libro/nuevo/index.html'])
            self.assertEqual(git('ls-files', '*.html').split(), nuevas)
            # Solo intención: el contenido no entra en el índice hasta el `git add` del llamador.
            self.assertEqual(git('diff', '--cached', '--name-only'), '')


if __name__ == '__main__':
    unittest.main()
