"""Clase de fallo del 14/11: un libro retirado y otro nuevo con HTML parecido salen como renombrado en el índice y
`línea[3:]` de `git status --porcelain` devolvía «a -> b», que la publicación rechazaba entera."""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import git_estado  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def git(cwd, *args):
    subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True)


class RutasTest(unittest.TestCase):
    def test_renombrado_y_tildes_salen_como_rutas_reales(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, 'init', '-q')
            git(repo, 'config', 'user.email', 'qa@example.invalid'); git(repo, 'config', 'user.name', 'qa')
            body = '<html>' + 'contenido de ficha muy parecido ' * 40 + '</html>'
            (repo / 'viejo').mkdir(); (repo / 'viejo/index.html').write_text(body, encoding='utf-8')
            git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'base')
            (repo / 'viejo/index.html').unlink()
            (repo / 'nuevo').mkdir(); (repo / 'nuevo/index.html').write_text(body + 'x', encoding='utf-8')
            (repo / 'canción con espacio.txt').write_text('a', encoding='utf-8')
            git(repo, 'add', '-A')
            self.assertIn('->', subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo, text=True))
            self.assertEqual(sorted(git_estado.rutas(repo)),
                             ['canción con espacio.txt', 'nuevo/index.html', 'viejo/index.html'])
            self.assertIn(('D ', 'viejo/index.html'), git_estado.entradas(repo))

    def test_ningun_publicador_corta_la_salida_de_porcelain(self):
        """Toda lista de rutas a publicar sale de git_estado, no de `línea[3:]` ni de `cut -c4-`.

        Cubre comillas simples y dobles, `--porcelain`, `--short` y `-s`, en Python, JS, shell y workflows."""
        asks = re.compile(r"""[^\n]*(?:--porcelain|--short|['"]status['"],\s*['"]-s['"]|git status -s\b)[^\n]*(?:\n[^\n]*)?""")
        offenders = []
        for base in ('scripts', 'qa', '.github'):
            for path in (ROOT / base).rglob('*'):
                if path.suffix not in ('.py', '.mjs', '.js', '.sh', '.yml', '.yaml') or path.name == 'git_estado.py':
                    continue
                text = path.read_text(encoding='utf-8', errors='ignore')
                for chunk in asks.findall(text):
                    cuts = '[3:]' in chunk or 'slice(3)' in chunk or 'cut -c4' in chunk
                    splits = 'splitlines' in chunk and '-z' not in chunk and '.strip()' not in chunk
                    if cuts or splits:
                        offenders.append(f'{path.relative_to(ROOT)}: {chunk.strip()[:90]}')
        self.assertEqual(offenders, [])

    def test_quien_importa_git_estado_se_puede_cargar_con_importlib(self):
        """14/11: reading-texts.py importaba git_estado sin su carpeta en sys.path y su test, que lo carga con
        importlib desde tests/, daba ModuleNotFoundError en la puerta de la PR."""
        missing = []
        for path in (ROOT / 'scripts').glob('*.py'):
            text = path.read_text(encoding='utf-8', errors='ignore')
            at = text.find('\nimport git_estado')
            if at >= 0 and path.name != 'git_estado.py' and 'sys.path.insert' not in text[:at]:
                missing.append(path.name)
        self.assertEqual(missing, [])

    def test_un_nombre_que_no_es_utf8_no_tumba_la_lectura(self):
        """#1312: `decode('utf-8')` estricto rompía toda la carga por un solo nombre en latin-1 (Linux lo permite)."""
        from unittest import mock
        salida = mock.Mock(stdout=b'?? caf\xe9.html\0?? bien.html\0')
        with mock.patch.object(git_estado.subprocess, 'run', return_value=salida):
            rutas = git_estado.rutas('.')
        self.assertEqual(rutas[1], 'bien.html')
        self.assertEqual(rutas[0].encode('utf-8', 'surrogateescape'), b'caf\xe9.html')

    def test_preparar_acepta_borrados_ya_preparados(self):
        """14/11 (#43579987645): `registrar` añadió la carpeta entera y `git add -- <borrada>` tumbó la carga."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, 'init', '-q')
            git(repo, 'config', 'user.email', 'qa@example.invalid'); git(repo, 'config', 'user.name', 'qa')
            body = '<html>' + 'contenido de ficha muy parecido ' * 40 + '</html>'
            for name in ('viejo', 'otro'):
                (repo / 'rec' / name).mkdir(parents=True); (repo / 'rec' / name / 'index.html').write_text(body + name, encoding='utf-8')
            git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'base')
            (repo / 'rec/viejo/index.html').unlink()
            (repo / 'rec/nuevo').mkdir(); (repo / 'rec/nuevo/index.html').write_text(body + 'x', encoding='utf-8')
            (repo / 'rec/otro/index.html').unlink()  # borrado sin preparar
            git(repo, 'add', '--', 'rec/viejo', 'rec/nuevo')  # lo que hace registrar con una carpeta
            git_estado.preparar(repo, git_estado.rutas(repo) + ['no-existe/ni-existió'])
            staged = subprocess.check_output(['git', 'diff', '--cached', '--name-status', '--no-renames'], cwd=repo, text=True)
            self.assertEqual(sorted(staged.splitlines()),
                             ['A	rec/nuevo/index.html', 'D	rec/otro/index.html', 'D	rec/viejo/index.html'])

    def test_preparar_miles_de_rutas_y_nombres_con_comodines(self):
        """Codex en #1312: miles de rutas en argv superan los 32 767 caracteres de Windows (WinError 206).
        Y `[ab]` no debe arrastrar otros ficheros como patrón."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, 'init', '-q')
            git(repo, 'config', 'user.email', 'qa@example.invalid'); git(repo, 'config', 'user.name', 'qa')
            carpeta = repo / ('recomendaciones-con-un-nombre-largo-' * 2)
            carpeta.mkdir()
            nombres = ['ficha-%04d-%s.html' % (i, 'x' * 30) for i in range(1200)]
            for n in nombres:
                (carpeta / n).write_text(n, encoding='utf-8')
            (repo / '[ab]').write_text('1', encoding='utf-8')
            (repo / 'a').write_text('2', encoding='utf-8')
            rutas = ['%s/%s' % (carpeta.name, n) for n in nombres] + ['[ab]']
            self.assertGreater(sum(len(r) + 1 for r in rutas), 32767)
            git_estado.preparar(repo, rutas)
            staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=repo, text=True).splitlines()
            self.assertEqual(len(staged), 1201)
            self.assertNotIn('a', staged)

    def test_ningun_publicador_prepara_listas_de_rutas_a_mano(self):
        """`git add -- *rutas` falla con borrados ya preparados: las listas van por git_estado.preparar."""
        star = re.compile(r"""['"]add['"],\s*(?:['"]-A['"],\s*)?['"]--['"],\s*\*""")
        offenders = [str(p.relative_to(ROOT)) for p in (ROOT / 'scripts').rglob('*.py')
                     if p.name != 'git_estado.py' and star.search(p.read_text(encoding='utf-8', errors='ignore'))]
        self.assertEqual(offenders, [])


if __name__ == '__main__':
    unittest.main()
