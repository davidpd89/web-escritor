import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('revision_existente', ROOT / 'scripts/revision_existente.py')
rev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rev)


def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class RevisionExistenteTests(unittest.TestCase):
    def test_grupos_cubren_todo_sin_repetir_y_con_tope(self):
        todos = rev.grupos()
        ficheros = [f for _, fs in todos for f in fs]
        self.assertEqual(len(ficheros), len(set(ficheros)))
        self.assertEqual([n for n, _ in todos[:len(rev.FIJOS)]], [n for n, _ in rev.FIJOS])
        for nombre, fs in todos[len(rev.FIJOS):]:
            if len(fs) > 1:
                self.assertLessEqual(sum(rev.lineas(f) for f in fs), rev.MAX_LINEAS, nombre)
        for nombre, fs in rev.FIJOS:  # un fichero fijo renombrado dejaría de revisarse sin avisar
            for f in fs:
                self.assertTrue((ROOT / f).exists(), f)

    def test_la_rotacion_empieza_por_la_carga_y_da_la_vuelta(self):
        self.assertEqual(rev.elegir(hoy=date(2026, 11, 14))[0], 'publicacion-carga')
        n = len(rev.grupos())
        self.assertEqual(rev.elegir(hoy=date.fromordinal(date(2026, 11, 14).toordinal() + n))[0], 'publicacion-carga')

    def test_la_pr_muestra_los_ficheros_enteros_y_no_toca_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen, repo = Path(tmp, 'origen.git'), Path(tmp, 'repo')
            git(tmp, 'init', '-q', '--bare', '-b', 'main', str(origen))
            git(tmp, 'clone', '-q', str(origen), str(repo))
            git(repo, 'config', 'user.email', 'qa@example.invalid')
            git(repo, 'config', 'user.name', 'qa')
            (repo / 'scripts').mkdir()
            for nombre in ('a.py', 'b.py', 'c.py'):
                (repo / 'scripts' / nombre).write_text('print(%r)\n' % nombre, encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'base')
            git(repo, 'push', '-q', 'origin', 'HEAD:main')
            main = git(repo, 'rev-parse', 'HEAD')
            llamadas = []

            def gh(*args):
                llamadas.append(args)
                if args[:2] == ('pr', 'list'):
                    return '[]'
                return 'https://github.com/x/y/pull/7' if args[:2] == ('pr', 'create') else ''

            with patch.object(rev, 'ROOT', repo), patch.object(rev, 'gh', gh), \
                    patch.object(rev, 'FIJOS', [('prueba', ['scripts/a.py', 'scripts/b.py'])]):
                rev.abrir('prueba', publicar=True)
            ramas = git(origen, 'for-each-ref', '--format=%(refname:short)', 'refs/heads/revision/').split()
            base = next(r for r in ramas if '/base-' in r)
            cabeza = next(r for r in ramas if r != base)
            self.assertEqual(git(origen, 'diff', '--name-status', base, cabeza).splitlines(),
                             ['A\tscripts/a.py', 'A\tscripts/b.py'])
            self.assertEqual(git(origen, 'rev-parse', cabeza + '^{tree}'), git(origen, 'rev-parse', 'main^{tree}'))
            self.assertEqual(git(origen, 'rev-parse', 'main'), main)
            self.assertEqual(git(repo, 'status', '--porcelain'), '')
            for rama in (base, cabeza):
                self.assertIn(rev.SKIP, git(origen, 'log', '-1', '--format=%B', rama))
            crear = next(a for a in llamadas if a[:2] == ('pr', 'create'))
            self.assertEqual(crear[crear.index('--base') + 1], base)
            self.assertNotIn('main', crear[crear.index('--base') + 1])
            self.assertEqual([a[4] for a in llamadas if a[:2] == ('pr', 'comment')], list(rev.DISPAROS))

    def test_workflows_van_como_copia_y_lo_que_no_esta_en_main_se_omite(self):
        """#1314 (CodeRabbit): el GITHUB_TOKEN no puede empujar commits que cambien .github/workflows/*, y un fichero
        del grupo que no está en origin/main hacía fallar `git rm --cached`."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, 'init', '-q')
            git(repo, 'config', 'user.email', 'qa@example.invalid')
            git(repo, 'config', 'user.name', 'qa')
            (repo / '.github/workflows').mkdir(parents=True)
            (repo / '.github/workflows/carga.yml').write_text('on: push\n', encoding='utf-8')
            (repo / 'a.py').write_text('print(1)\n', encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'base')
            main = git(repo, 'rev-parse', 'HEAD')
            with patch.object(rev, 'ROOT', repo):
                base, cabeza = rev.arboles(main, ['a.py', '.github/workflows/carga.yml', 'solo-local.py'], 'x')
            tocados = git(repo, 'log', '--format=', '--name-only', main + '..' + cabeza).split()
            self.assertFalse([t for t in tocados if t.startswith('.github/')], tocados)
            self.assertEqual(git(repo, 'diff', '--name-status', base, cabeza).splitlines(),
                             ['A\t_revision/.github/workflows/carga.yml', 'A\ta.py'])
            self.assertEqual(git(repo, 'show', cabeza + ':_revision/.github/workflows/carga.yml'), 'on: push')
            with patch.object(rev, 'ROOT', repo), self.assertRaises(SystemExit):
                rev.arboles(main, ['solo-local.py'], 'x')

    def test_un_reintento_reutiliza_la_pr_y_solo_completa_los_disparos(self):
        """#1314: un segundo intento del mismo día no empuja ramas ni crea PR; solo pide lo que faltó."""
        llamadas, empujes = [], []

        def gh(*args):
            llamadas.append(args)
            if args[:2] == ('pr', 'list'):
                return json.dumps([{'url': 'https://github.com/x/y/pull/9',
                                    'comments': [{'body': rev.DISPAROS[0] + chr(10)}]}])
            return ''

        def git(*args, **_):  # sin red ni repo: solo importa que no se empuje nada
            if args[:1] == ('push',):
                empujes.append(args)
            return 'f' * 40

        with patch.object(rev, 'gh', gh), patch.object(rev, 'git', git),                 patch.object(rev, 'FIJOS', [('prueba', ['scripts/revision_existente.py'])]):
            rev.abrir('prueba', publicar=True)
        self.assertEqual(empujes, [])
        self.assertFalse([a for a in llamadas if a[:2] == ('pr', 'create')])
        self.assertEqual([a[2:] for a in llamadas if a[:2] == ('pr', 'comment')],
                         [('9', '--body', rev.DISPAROS[1])])


if __name__ == '__main__':
    unittest.main()
