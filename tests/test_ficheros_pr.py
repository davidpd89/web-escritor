"""Caso 22 de la ronda 2 GPT (25/11): la API de ficheros de una PR corta en 3000 y una carga cambia ~11 000.

La guarda de rutas permitidas de los publicadores tiene que ver la lista entera: por encima del tope sale de git.
"""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publicador_ficheros', ROOT / 'scripts/publish-radar-refresh.py')
pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)


def run(*args, cwd):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class FicherosPrTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        origin, self.clone = base / 'origin.git', base / 'clone'
        run('init', '-q', '--bare', '-b', 'main', str(origin), cwd=base)
        run('clone', '-q', str(origin), str(self.clone), cwd=base)
        for k, v in (('user.name', 't'), ('user.email', 't@t')):
            run('config', k, v, cwd=self.clone)
        (self.clone / 'data').mkdir()
        (self.clone / 'data/a.json').write_text('{"a": "uno dos tres cuatro cinco seis"}\n', encoding='utf-8')
        run('add', '.', cwd=self.clone)
        run('commit', '-q', '-m', 'base', cwd=self.clone)
        run('push', '-q', 'origin', 'HEAD:main', cwd=self.clone)
        run('switch', '-q', '-c', 'automation/x', cwd=self.clone)
        run('mv', 'data/a.json', 'data/e.json', cwd=self.clone)
        for n in 'bcd':
            (self.clone / f'data/{n}.json').write_text('{}\n', encoding='utf-8')
        (self.clone / 'scripts').mkdir()
        (self.clone / 'scripts/colado.py').write_text('x = 1\n', encoding='utf-8')
        run('add', '.', cwd=self.clone)
        run('commit', '-q', '-m', 'carga', cwd=self.clone)
        self.head = run('rev-parse', 'HEAD', cwd=self.clone)
        run('push', '-q', 'origin', 'HEAD:automation/x', cwd=self.clone)
        # main avanza después: lo suyo no es de la PR
        run('switch', '-q', '--detach', 'origin/main', cwd=self.clone)
        (self.clone / 'z.txt').write_text('z\n', encoding='utf-8')
        run('add', '.', cwd=self.clone)
        run('commit', '-q', '-m', 'main avanza', cwd=self.clone)
        run('push', '-q', 'origin', 'HEAD:main', cwd=self.clone)
        self.git = lambda *a: pub._git_salida(*a, cwd=self.clone)

    def api(self, n):
        return lambda *args: json.dumps([[{'filename': f'data/{i}.json'} for i in range(n)]])

    def test_por_debajo_del_tope_vale_la_api(self):
        items = pub.ficheros_pr('o/r', {'number': 1, 'headRefOid': self.head}, gh_=self.api(2), git=None, tope=3)
        self.assertEqual(len(items), 2)

    def test_en_el_tope_la_lista_sale_de_git_con_lo_que_la_api_no_ensena(self):
        items = pub.ficheros_pr('o/r', {'number': 1, 'headRefOid': self.head}, gh_=self.api(3), git=self.git, tope=3)
        nombres = sorted(i['filename'] for i in items)
        self.assertEqual(nombres, ['data/b.json', 'data/c.json', 'data/d.json', 'data/e.json', 'scripts/colado.py'])
        self.assertIn({'filename': 'data/e.json', 'previous_filename': 'data/a.json'}, items)
        self.assertNotIn('z.txt', nombres, 'lo que main cambió después no cuenta como de la PR')

    def test_si_git_ve_menos_que_la_api_no_se_da_por_buena(self):
        with self.assertRaises(ValueError):
            pub.ficheros_pr('o/r', {'number': 1, 'headRefOid': self.head}, gh_=self.api(9), git=self.git, tope=3)

    def test_los_publicadores_no_leen_la_api_de_ficheros_por_su_cuenta(self):
        for nombre in ('publish-radar-refresh.py', 'publish-reading-refresh.py'):
            fuente = (ROOT / 'scripts' / nombre).read_text(encoding='utf-8')
            with self.subTest(nombre):
                self.assertEqual(fuente.count('/files?per_page'), int(nombre == 'publish-radar-refresh.py'),
                                 'una lectura suelta del listado vuelve a cortar en 3000')


if __name__ == '__main__':
    unittest.main()
