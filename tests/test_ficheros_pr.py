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

    def test_si_la_api_no_puede_generar_el_diff_la_lista_sale_de_git(self):
        """27/11, carga 46028944813: HTTP 422 «diff taking too long» con 10 419 libros tumbó la carga."""
        def api_rota(*args):
            raise subprocess.CalledProcessError(1, ['gh', *args], stderr='HTTP 422: this diff is taking too long')
        items = pub.ficheros_pr('o/r', {'number': 1, 'headRefOid': self.head}, gh_=api_rota, git=self.git, tope=3)
        self.assertEqual(sorted(i['filename'] for i in items),
                         ['data/b.json', 'data/c.json', 'data/d.json', 'data/e.json', 'scripts/colado.py'])

    def test_si_la_api_agota_el_tiempo_la_lista_sale_de_git(self):
        """Revisión de CodeRabbit en #1622: gh() relanza TimeoutExpired tras agotar sus reintentos."""
        def api_lenta(*args):
            raise subprocess.TimeoutExpired(['gh', *args], 600)
        items = pub.ficheros_pr('o/r', {'number': 1, 'headRefOid': self.head}, gh_=api_lenta, git=self.git, tope=3)
        self.assertEqual(len(items), 5)

    def test_sin_api_ni_git_falla_en_vez_de_dar_lista_vacia(self):
        def api_rota(*args):
            raise subprocess.CalledProcessError(1, ['gh', *args])
        def git_roto(*args):
            raise subprocess.CalledProcessError(128, ['git', *args])
        with self.assertRaises(subprocess.CalledProcessError):
            pub.ficheros_pr('o/r', {'number': 1, 'headRefOid': self.head}, gh_=api_rota, git=git_roto, tope=3)

    def test_los_publicadores_no_leen_la_api_de_ficheros_por_su_cuenta(self):
        for nombre in ('publish-radar-refresh.py', 'publish-reading-refresh.py'):
            fuente = (ROOT / 'scripts' / nombre).read_text(encoding='utf-8')
            with self.subTest(nombre):
                self.assertEqual(fuente.count('/files?per_page'), int(nombre == 'publish-radar-refresh.py'),
                                 'una lectura suelta del listado vuelve a cortar en 3000')


    # 27/11, carga 46054825375: la API compare también genera el diff entero y da 422 con una carga grande.
    def api_422(self, *args):
        raise subprocess.CalledProcessError(1, ['gh', *args], stderr='HTTP 422: this diff is taking too long')

    def test_compare_con_la_api_rota_sale_de_git(self):
        data = pub.comparar('o/r', 'main', self.head, gh_=self.api_422, git=self.git)
        self.assertEqual((data['status'], data['ahead_by'], data['behind_by']), ('diverged', 1, 1))

    def test_compare_con_ficheros_sale_de_git_completo(self):
        data = pub.comparar('o/r', 'main', self.head, ficheros=True, gh_=self.api_422, git=self.git)
        self.assertTrue(data['completa'])
        self.assertEqual(sorted(i['filename'] for i in data['files']),
                         ['data/b.json', 'data/c.json', 'data/d.json', 'data/e.json', 'scripts/colado.py'])

    def test_compare_truncado_por_la_api_se_completa_con_git(self):
        truncada = lambda *a: json.dumps({'status': 'diverged', 'ahead_by': 1, 'behind_by': 1,
                                          'files': [{'filename': f'x/{i}'} for i in range(300)]})
        data = pub.comparar('o/r', 'main', self.head, ficheros=True, gh_=truncada, git=self.git)
        self.assertEqual(len(data['files']), 5)

    def test_compare_truncado_y_sin_git_devuelve_lo_de_la_api(self):
        truncada = lambda *a: json.dumps({'ahead_by': 1, 'files': [{'filename': f'x/{i}'} for i in range(300)]})
        def git_roto(*args):
            raise subprocess.CalledProcessError(128, ['git', *args])
        data = pub.comparar('o/r', 'a', 'b', ficheros=True, gh_=truncada, git=git_roto)
        self.assertEqual(len(data['files']), 300)
        self.assertNotIn('completa', data)

    def test_estado_con_la_api_rota_sale_de_git(self):
        main = self.git('rev-parse', 'origin/main').strip()
        self.assertEqual(pub.estado_comparacion('o/r', self.head, main, gh_=self.api_422, git=self.git), 'diverged')
        self.assertEqual(pub.estado_comparacion('o/r', self.head, self.head, gh_=self.api_422, git=self.git), 'identical')

    def test_sin_api_ni_git_la_comparacion_falla(self):
        def git_roto(*args):
            raise subprocess.CalledProcessError(128, ['git', *args])
        with self.assertRaises(subprocess.CalledProcessError):
            pub.comparar('o/r', 'a', 'b', gh_=self.api_422, git=git_roto)

    def test_los_publicadores_no_llaman_a_compare_por_su_cuenta(self):
        """Una llamada suelta a la API compare vuelve a tumbar la carga con 422 en un diff grande."""
        for nombre in ('publish-radar-refresh.py', 'publish-reading-refresh.py'):
            fuente = (ROOT / 'scripts' / nombre).read_text(encoding='utf-8')
            with self.subTest(nombre):
                self.assertEqual(fuente.count('/compare/'), 2 * int(nombre == 'publish-radar-refresh.py'))


if __name__ == '__main__':
    unittest.main()
