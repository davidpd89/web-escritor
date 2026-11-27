"""Carga 46054825375 (27/11): con 10 419 libros `compare/main...<cabeza>` responde HTTP 422 («this diff is taking
too long to generate») y resume_pending tumbaba la carga. Toda comparación del publicador pasa por `comparar`:
si la API no puede, el estado sale de git en un repo real; si git tampoco, falla en vez de inventar un estado.
"""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publicador_comparar', ROOT / 'scripts/publish-radar-refresh.py')
pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)


def run(*args, cwd):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def api_422(*args):
    raise subprocess.CalledProcessError(1, ['gh', *args], stderr='Sorry, this diff is taking too long to generate. (HTTP 422)')


class CompararTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        origin, self.clone = base / 'origin.git', base / 'clone'
        run('init', '-q', '--bare', '-b', 'main', str(origin), cwd=base)
        run('clone', '-q', str(origin), str(self.clone), cwd=base)
        for k, v in (('user.name', 't'), ('user.email', 't@t')):
            run('config', k, v, cwd=self.clone)
        (self.clone / 'a.txt').write_text('a\n', encoding='utf-8')
        run('add', '.', cwd=self.clone)
        run('commit', '-q', '-m', 'base', cwd=self.clone)
        run('push', '-q', 'origin', 'HEAD:main', cwd=self.clone)
        self.base = run('rev-parse', 'HEAD', cwd=self.clone)
        run('switch', '-q', '-c', 'automation/x', cwd=self.clone)
        (self.clone / 'data.json').write_text('{}\n', encoding='utf-8')
        run('add', '.', cwd=self.clone)
        run('commit', '-q', '-m', 'datos', cwd=self.clone)
        self.head = run('rev-parse', 'HEAD', cwd=self.clone)
        run('push', '-q', 'origin', 'automation/x', cwd=self.clone)
        self.git = partial(pub._git_salida, cwd=self.clone)

    def avanzar_main(self):
        run('switch', '-q', 'main', cwd=self.clone)
        (self.clone / 'scripts.py').write_text('x = 1\n', encoding='utf-8')
        run('add', '.', cwd=self.clone)
        run('commit', '-q', '-m', 'codigo', cwd=self.clone)
        run('push', '-q', 'origin', 'HEAD:main', cwd=self.clone)

    def test_con_api_devuelve_lo_que_da_la_api(self):
        visto = []
        api = lambda *a: visto.append(a) or json.dumps({'status': 'ahead', 'ahead_by': 1, 'behind_by': 0, 'files': []})
        self.assertEqual(pub.comparar('o/r', 'main', 'abc', gh_=api)['behind_by'], 0)
        self.assertEqual(visto, [('api', 'repos/o/r/compare/main...abc')])
        self.assertEqual(pub.comparar('o/r', 'a', 'b', jq='.status', gh_=lambda *a: 'identical'), 'identical')

    def test_api_422_y_main_detras_sale_de_git(self):
        data = pub.comparar('o/r', 'main', self.head, gh_=api_422, git=self.git)
        self.assertEqual((data['status'], data['ahead_by'], data['behind_by']), ('ahead', 1, 0))
        self.assertEqual(data['files'], [{'filename': 'data.json'}])
        self.assertTrue(data['completo'])

    def test_api_422_con_main_avanzado_ve_behind_by(self):
        self.avanzar_main()
        data = pub.comparar('o/r', 'main', self.head, gh_=api_422, git=self.git)
        self.assertEqual((data['status'], data['ahead_by'], data['behind_by']), ('diverged', 1, 1))
        # Como la API de tres puntos: solo lo que trae la cabeza desde la base común.
        self.assertEqual(data['files'], [{'filename': 'data.json'}])
        # Sentido inverso (main_cambio_qa): lo que main tiene y la cabeza no.
        inverso = pub.comparar('o/r', self.head, 'main', gh_=api_422, git=self.git)
        self.assertEqual([f['filename'] for f in inverso['files']], ['scripts.py'])

    def test_jq_status_sin_api(self):
        self.assertEqual(pub.comparar('o/r', self.base, self.head, jq='.status', gh_=api_422, git=self.git), 'ahead')
        self.assertEqual(pub.comparar('o/r', self.head, self.base, jq='.status', gh_=api_422, git=self.git), 'behind')
        self.assertEqual(pub.comparar('o/r', self.head, self.head, jq='.status', gh_=api_422, git=self.git), 'identical')

    def test_sin_api_ni_git_falla(self):
        def git_roto(*args):
            raise subprocess.CalledProcessError(128, ['git', *args])
        with self.assertRaises(subprocess.CalledProcessError):
            pub.comparar('o/r', 'main', self.head, gh_=api_422, git=git_roto)

    def test_lista_completa_de_git_no_se_toma_por_truncada(self):
        files = [{'filename': f'pagina-{n}.html'} for n in range(400)] + [{'filename': 'qa/x.mjs'}]
        datos = {'ahead_by': 1, 'files': files, 'completo': True}
        original = pub.comparar
        pub.comparar = lambda *a, **k: datos
        try:
            self.assertEqual(pub.main_cambio_qa('o/r', 'sha'), ['qa/x.mjs'])
        finally:
            pub.comparar = original

    def test_ninguna_llamada_directa_a_compare_fuera_de_comparar(self):
        for nombre in ('publish-radar-refresh.py', 'publish-reading-refresh.py'):
            fuente = (ROOT / 'scripts' / nombre).read_text(encoding='utf-8')
            usos = [l for l in fuente.splitlines() if '/compare/' in l and 'def comparar' not in l]
            permitidos = [l for l in usos if "f'repos/{repo}/compare/{base}...{head}'" in l or l.strip().startswith('"""`gh api')]
            self.assertEqual(usos, permitidos, f'{nombre}: compare directo sin respaldo de git')


if __name__ == '__main__':
    unittest.main()
