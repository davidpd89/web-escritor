"""F4 (R4-3): la cuarentena no puede seguir sin la versión publicada del catálogo.

Con `previous=None` todo libro cuenta como nuevo: el tope crece al catálogo entero y los libros publicados se
apartan (se borran de la web) en vez de volver a su versión buena. Si `git show HEAD:<catálogo>` falla, la
cuarentena aborta; solo un HEAD que de verdad no tiene catálogo (no hay nada publicado) da `None`.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_quarantine as q  # noqa: E402

CATALOGO = {'schema_version': 1, 'categorias': [], 'libros': [{'id': 'publicado-uno', 'estado': 'publicado'}],
            'libro_categorias': []}


GIT = shutil.which('git') or 'git'
_GIT_ENV = {}


def setUpModule():
    # Un hook o un worktree pueden dejar GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE: el repo temporal sería el de fuera.
    for clave in [k for k in os.environ if k.startswith('GIT_')]:
        _GIT_ENV[clave] = os.environ.pop(clave)


def tearDownModule():
    os.environ.update(_GIT_ENV)


def git(root, *args):
    subprocess.run([GIT, *args], cwd=root, check=True, capture_output=True)


def arbol(root, commit=True):
    path = root / q.CATALOGUE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(CATALOGO), encoding='utf-8')
    git(root, 'init', '-q')
    git(root, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'vacio')
    if commit:
        git(root, 'add', '.')
        git(root, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'catalogo')
    return path


class VersionPublicadaTest(unittest.TestCase):
    def test_lee_la_version_publicada(self):
        with tempfile.TemporaryDirectory() as tmp:
            arbol(Path(tmp))
            self.assertEqual(q.committed(Path(tmp))['libros'][0]['id'], 'publicado-uno')

    def test_sin_catalogo_en_head_no_hay_nada_publicado(self):
        with tempfile.TemporaryDirectory() as tmp:
            arbol(Path(tmp), commit=False)
            self.assertIsNone(q.committed(Path(tmp)))

    def test_si_git_falla_aborta(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / q.CATALOGUE).parent.mkdir(parents=True)
            (root / q.CATALOGUE).write_text(json.dumps(CATALOGO), encoding='utf-8')  # sin repo git
            with self.assertRaises(RuntimeError):
                q.committed(root)

    def test_si_la_version_publicada_esta_rota_aborta(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = arbol(root)
            path.write_text('{roto', encoding='utf-8')
            git(root, 'add', '.')
            git(root, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'roto')
            with self.assertRaises(RuntimeError):
                q.committed(root)

    def test_apply_aborta_sin_tocar_el_catalogo(self):
        """Ningún libro publicado desaparece: el catálogo del árbol queda como estaba."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / q.CATALOGUE
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(CATALOGO), encoding='utf-8')
            antes = path.read_bytes()
            with self.assertRaises(RuntimeError):
                q.apply(root, today='2026-11-16')
            self.assertEqual(path.read_bytes(), antes)
            self.assertFalse((root / q.QUARANTINE).exists())


if __name__ == '__main__':
    unittest.main()
