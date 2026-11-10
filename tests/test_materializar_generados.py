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


# Workflows que sirven el árbol con http.server y aún no materializan con la acción. Trinquete: solo puede encoger.
# Al adoptar la acción en uno, se quita de aquí; uno nuevo con http.server debe nacer usándola.
PENDIENTES_DE_MATERIALIZAR = {
    'a11y-regressions-browser-qa.yml',
    'assistant-hardening-qa.yml',
    'atlas-catalogue-qa.yml',
    'autor-browser-qa.yml',
    'content-parity-manecillas.yml',
    'convocatorias-browser-qa.yml',
    'cross-engine-smoke.yml',
    'cuaderno-browser-qa.yml',
    'cuaderno-topics-browser-qa.yml',
    'design-evidence-hardening.yml',
    'editoriales-browser-qa.yml',
    'eventos-browser-qa.yml',
    'ferias-archive-parity-qa.yml',
    'ferias-browser-qa.yml',
    'findability-browser-qa.yml',
    'global-discoverability-closure-qa.yml',
    'home-map-interaction-qa.yml',
    'identity-public-browser-qa.yml',
    'machine-authority-check.yml',
    'manecillas-fragments-nav-qa.yml',
    'mejoras-web-preview.yml',
    'metodologia-editorial-browser-qa.yml',
    'newsletter-consent-qa.yml',
    'pa11y-baseline.yml',
    'postdeploy-deep-audit.yml',
    'premios-browser-qa.yml',
    'prensa-browser-qa.yml',
    'privacy-legal-browser-qa.yml',
    'pro-resources-qa.yml',
    'reading-failure-resilience.yml',
    'recommendations-browser-qa.yml',
    'samuel-ecosystem-browser-qa.yml',
    'sitewide-reflow-qa.yml',
    'tools-browser-qa.yml',
    'tools-events-memory-browser-qa.yml',
    'tools-publishing-browser-qa.yml',
    'tools-structure-browser-qa.yml',
}
ACCION = './.github/actions/materializar'


class AccionMaterializar(unittest.TestCase):
    def test_la_accion_usa_la_cadena_unica(self):
        texto = (ROOT / '.github/actions/materializar/action.yml').read_text(encoding='utf-8')
        self.assertIn('scripts/materializar_generados.py --solo-construir', texto)
        self.assertIn('actions/cache/restore', texto)

    def test_trinquete_de_workflows_con_http_server(self):
        sin_accion = set()
        for wf in (ROOT / '.github/workflows').glob('*.yml'):
            texto = wf.read_text(encoding='utf-8')
            if 'http.server' in texto and ACCION not in texto:
                sin_accion.add(wf.name)
        self.assertEqual(sin_accion - PENDIENTES_DE_MATERIALIZAR, set(),
                         'workflow nuevo con http.server sin la acción materializar')
        self.assertEqual(PENDIENTES_DE_MATERIALIZAR - sin_accion, set(),
                         'ya usa la acción (o no existe): quítalo de PENDIENTES_DE_MATERIALIZAR')


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
