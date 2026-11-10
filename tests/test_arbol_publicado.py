"""El árbol publicado (scripts/arbol_publicado.py) y el trinquete que obliga a usarlo.

Antes del corte de la fase 5, lo generado sale de git; después, solo del disco. Si un check sigue con
`git ls-files` a pelo, deja de mirar ~6800 páginas sin fallar. Por eso:
  - hoy, con lo generado versionado, el árbol publicado es byte a byte `git ls-files`;
  - quitado del índice (simulando el corte), sigue listando lo mismo;
  - ningún script, test ni qa/*.mjs llama a `git ls-files` sin pasar por él (salvo los que preguntan por el índice).
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import arbol_publicado  # noqa: E402

# Preguntan por el índice de git, no por lo publicado: materializar (qué está versionado), la fusión (conflictos),
# la carga (qué rutas de datos versiona) y su test.
PREGUNTAN_AL_INDICE = {
    'scripts/arbol_publicado.py', 'scripts/materializar_generados.py', 'scripts/merge-main.py',
    'scripts/refresh-reading-catalogue.py', 'tests/test_materializar_generados.py', 'tests/test_arbol_publicado.py',
}
FORMAS = (
    ['git', 'ls-files', '-z', '*.html'],
    ['git', 'ls-files', '*.html'],
    ['git', '-c', 'core.quotepath=false', 'ls-files', '-z', '*.html'],
    ['git', 'ls-files', '-z', '--', '*.js'],
    ['git', 'ls-files', 'recomendaciones/**/index.html'],
    ['git', 'ls-files'],
)


def _git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True)


class Repo(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        _git(self.dir, 'init', '-q')
        for rel in ('index.html', 'libros/index.html', 'recomendaciones/a/index.html', 'recomendaciones/año.html',
                    'editoriales/x.html', 'sitemap.xml', 'sitemap-libros.xml', 'assets/page-order.generated.js',
                    'assets/app.js', 'pagefind/pagefind.js', 'notas/borrador.html'):
            (self.dir / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.dir / rel).write_text('x', encoding='utf-8')
        (self.dir / '.gitignore').write_text('notas/\n', encoding='utf-8')
        _git(self.dir, 'add', '-A')

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def todas(self):
        return {tuple(f): subprocess.check_output(f, cwd=self.dir) for f in FORMAS}

    def test_con_lo_generado_versionado_es_igual_que_git(self):
        for forma, esperado in self.todas().items():
            self.assertEqual(arbol_publicado.check_output(list(forma), cwd=self.dir), esperado, forma)

    def test_tras_el_corte_lista_lo_mismo(self):
        antes = self.todas()
        _git(self.dir, 'rm', '-r', '-q', '--cached', 'recomendaciones', 'editoriales', 'pagefind', 'sitemap.xml',
             'sitemap-libros.xml', 'assets/page-order.generated.js')
        with open(self.dir / '.gitignore', 'a', encoding='utf-8') as f:
            f.write('recomendaciones/\neditoriales/\npagefind/\nsitemap*.xml\nassets/page-order.generated.js\n')
        _git(self.dir, 'add', '.gitignore')
        for forma, esperado in antes.items():
            visto = arbol_publicado.check_output(list(forma), cwd=self.dir)
            self.assertEqual(visto, esperado, forma)
        self.assertNotIn(b'notas/', arbol_publicado.check_output(['git', 'ls-files'], cwd=self.dir))

    def test_imita_los_tipos_de_subprocess(self):
        r = arbol_publicado.run(['git', 'ls-files', '*.html'], cwd=self.dir, capture_output=True, text=True)
        self.assertIsInstance(r.stdout, str)
        self.assertEqual(r.returncode, 0)
        self.assertIsInstance(arbol_publicado.check_output(['git', 'ls-files'], cwd=self.dir), bytes)
        self.assertIn('"recomendaciones/a\\303\\261o.html"', r.stdout)   # citado como git

    def test_otras_preguntas_van_a_git_tal_cual(self):
        self.assertEqual(arbol_publicado.check_output(['git', 'ls-files', '--others'], cwd=self.dir),
                         subprocess.check_output(['git', 'ls-files', '--others'], cwd=self.dir))
        with self.assertRaises(subprocess.CalledProcessError):
            arbol_publicado.run(['git', 'rev-parse', '--verify', 'no-existe'], cwd=self.dir, capture_output=True,
                                check=True)

    def test_tras_el_corte_sin_materializar_materializa_antes_de_listar(self):
        _git(self.dir, 'rm', '-r', '-q', '--cached', 'recomendaciones', 'assets/page-order.generated.js')
        shutil.rmtree(self.dir / 'recomendaciones')
        (self.dir / 'assets/page-order.generated.js').unlink()
        builder = self.dir / 'scripts' / 'materializar_generados.py'
        builder.parent.mkdir()
        builder.write_text(
            "import pathlib\n"
            "print('construyendo')\n"
            "for r in ('recomendaciones/a/index.html', 'assets/page-order.generated.js'):\n"
            "    pathlib.Path(r).parent.mkdir(parents=True, exist_ok=True)\n"
            "    pathlib.Path(r).write_text('x')\n", encoding='utf-8')
        cli = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'arbol_publicado.py'), '*.html'],
                             cwd=self.dir, capture_output=True, check=True)
        self.assertIn(b'recomendaciones/a/index.html', cli.stdout.splitlines())
        self.assertNotIn(b'construyendo', cli.stdout)   # la salida del builder no ensucia el listado

    def test_en_ci_avisa_en_el_resumen_del_job(self):
        _git(self.dir, 'rm', '-r', '-q', '--cached', 'assets/page-order.generated.js')
        (self.dir / 'assets/page-order.generated.js').unlink()
        builder = self.dir / 'scripts' / 'materializar_generados.py'
        builder.parent.mkdir()
        builder.write_text("import pathlib\npathlib.Path('assets/page-order.generated.js').write_text('x')\n",
                           encoding='utf-8')
        resumen = self.dir / 'resumen.md'
        entorno = {**os.environ, 'GITHUB_STEP_SUMMARY': str(resumen), 'GITHUB_WORKFLOW': 'QA', 'GITHUB_JOB': 'enlaces'}
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'arbol_publicado.py'), '*.html'], cwd=self.dir,
                       capture_output=True, check=True, env=entorno)
        self.assertIn('`QA` / `enlaces`', resumen.read_text(encoding='utf-8'))

    def test_la_cli_da_lo_mismo_que_git(self):
        cli = subprocess.check_output([sys.executable, str(ROOT / 'scripts' / 'arbol_publicado.py'), '-z', '*.html'],
                                      cwd=self.dir)
        self.assertEqual(cli, subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=self.dir))


def _llama_a_ls_files(nodo: ast.Call) -> bool:
    directos = [a for a in nodo.args if not isinstance(a, ast.Call)]   # .decode().split() no es la llamada
    valores = [c.value for a in directos for c in ast.walk(a) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
    if 'ls-files' not in valores:
        return False
    f = nodo.func
    return not (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == 'arbol_publicado')


class Trinquete(unittest.TestCase):
    def test_nadie_lista_el_arbol_con_git_ls_files_a_pelo(self):
        ficheros = subprocess.check_output(['git', 'ls-files', '--', 'scripts/*.py', 'tests/*.py', 'qa/*.py'],
                                           cwd=ROOT, text=True).split()
        malos = []
        for rel in ficheros:
            if rel in PREGUNTAN_AL_INDICE:
                continue
            texto = (ROOT / rel).read_text(encoding='utf-8')
            if 'ls-files' not in texto:
                continue
            for nodo in ast.walk(ast.parse(texto)):
                if isinstance(nodo, ast.Call) and _llama_a_ls_files(nodo):
                    malos.append(f'{rel}:{nodo.lineno}')
        self.assertEqual(malos, [], 'usa arbol_publicado.run/check_output (o listar): tras el corte, git no ve lo generado')

    def test_los_mjs_tampoco(self):
        ficheros = subprocess.check_output(['git', 'ls-files', '--', '*.mjs', '*.js', '*.cjs'], cwd=ROOT, text=True)
        malos = []
        for rel in ficheros.split():
            if rel.startswith(('node_modules/', 'research/vendor/')):
                continue
            texto = (ROOT / rel).read_text(encoding='utf-8', errors='replace')
            if re.search(r"""['"]ls-files['"]""", texto):
                malos.append(rel)
        self.assertEqual(malos, [], 'en Node, usa qa/arbol-publicado.mjs')


if __name__ == '__main__':
    unittest.main()
