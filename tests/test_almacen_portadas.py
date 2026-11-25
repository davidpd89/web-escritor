import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import almacen_portadas as almacen  # noqa: E402
import reading_cover_store as store  # noqa: E402

BASE = 'https://davidpd89.github.io/web-escritor-portadas'


def git(*args, cwd):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


class AlmacenPortadasTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root, self.remote, self.clone = base / 'web', base / 'remoto.git', base / 'almacen'
        (self.root / 'data').mkdir(parents=True)
        (self.root / almacen.LOCAL).mkdir(parents=True)
        (self.root / store.MANIFEST).write_text(json.dumps({'base_url': BASE, 'archivos': ['autor.webp'], 'sha256': {'autor.webp': store.digest(b'autor')}}), encoding='utf-8')
        for name, content in (('isbn-1.webp', b'uno'), ('isbn-2.webp', b'dos')):
            (self.root / almacen.LOCAL / name).write_bytes(content)
        git('init', '-q', '--bare', '-b', 'main', str(self.remote), cwd=base)
        git('clone', '-q', str(self.remote), str(self.clone), cwd=base)
        git('config', 'user.name', 't', cwd=self.clone)
        git('config', 'user.email', 't@t', cwd=self.clone)
        (self.clone / 'autor.webp').write_bytes(b'autor')
        git('add', '.', cwd=self.clone)
        git('commit', '-qm', 'inicio', cwd=self.clone)
        git('push', '-q', 'origin', 'main', cwd=self.clone)
        for env in (store.STORE_DIR_ENV, store.STORE_URL_ENV):
            saved = os.environ.pop(env, None)
            self.addCleanup(lambda e=env, v=saved: os.environ.__setitem__(e, v) if v else os.environ.pop(e, None))

    def test_el_cupo_avisa_antes_de_llenarse_y_no_para_la_carga_si_no_sabe_el_tamano(self):
        self.assertEqual(almacen.cupo(None), 'ok')
        self.assertEqual(almacen.cupo(3_700), 'ok')
        self.assertEqual(almacen.cupo(almacen.AVISO_KB), 'aviso')
        self.assertEqual(almacen.cupo(almacen.LLENO_KB), 'lleno')
        self.assertLess(almacen.LLENO_KB, 1024 * 1024)  # por debajo del GB de Pages

    def test_migrar_sube_y_registra_sin_borrar_y_verificar_solo_borra_lo_que_pages_sirve(self):
        self.assertEqual(almacen.migrar(self.root, self.clone, BASE), 2)
        subidas = git('ls-tree', '--name-only', 'main', cwd=self.remote).split()
        self.assertEqual(sorted(subidas), ['autor.webp', 'isbn-1.webp', 'isbn-2.webp'])
        self.assertEqual(store.names(self.root), {'autor.webp', 'isbn-1.webp', 'isbn-2.webp'})
        self.assertTrue((self.root / almacen.LOCAL / 'isbn-1.webp').is_file())  # migrar no borra
        self.assertEqual(almacen.migrar(self.root, self.clone, BASE), 0)  # repetirla no hace nada
        # Pages aún no sirve isbn-2: esa copia local se queda
        servidas = {f'{BASE}/isbn-1.webp'}
        borradas, fallidas = almacen.verificar(self.root, borrar=True, probe=lambda url, sha: url in servidas)
        self.assertEqual((borradas, fallidas), (1, ['isbn-2.webp']))
        self.assertFalse((self.root / almacen.LOCAL / 'isbn-1.webp').exists())
        self.assertTrue((self.root / almacen.LOCAL / 'isbn-2.webp').is_file())

    def test_un_fallo_suelto_de_pages_no_cuenta_como_ausente(self):
        respuestas = iter([False, False, True])
        self.assertTrue(almacen._responde('u', 'h', get=lambda u, h: next(respuestas), espera=lambda s: None))
        self.assertFalse(almacen._responde('u', 'h', get=lambda u, h: False, espera=lambda s: None))

    def test_un_200_con_otros_bytes_no_autoriza_a_borrar(self):
        class Res:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b'otra cosa'
        from unittest import mock
        with mock.patch.object(almacen.urllib.request, 'urlopen', return_value=Res()):
            self.assertFalse(almacen._get('https://x/isbn-1.webp', store.digest(b'uno')))
            self.assertTrue(almacen._get('https://x/isbn-1.webp', store.digest(b'otra cosa')))

    def test_migrar_exige_la_url_del_almacen_de_destino(self):
        with self.assertRaisesRegex(ValueError, 'URL https'):
            almacen.migrar(self.root, self.clone, '')
        self.assertFalse((self.clone / 'isbn-1.webp').exists())  # nada copiado
        segundo = BASE + '-2'
        almacen.migrar(self.root, self.clone, segundo)
        data = store.load(self.root)
        self.assertEqual(store.url_of(data, 'isbn-1.webp'), segundo)
        self.assertEqual(store.url_of(data, 'autor.webp'), BASE)

    def test_repetir_migrar_vuelve_a_subir_lo_registrado_aunque_no_haya_pendientes(self):
        from unittest import mock
        real = store.flush
        with mock.patch.object(store, 'flush', side_effect=RuntimeError('red')):
            with self.assertRaises(RuntimeError):
                almacen.migrar(self.root, self.clone, BASE)
        self.assertEqual(almacen.migrar(self.root, self.clone, BASE), 0)  # sin pendientes, pero sube
        subidas = git('ls-tree', '--name-only', 'main', cwd=self.remote).split()
        self.assertIn('isbn-1.webp', subidas)
        self.assertIs(store.flush, real)

    def test_una_copia_local_cambiada_despues_de_migrar_no_se_borra(self):
        almacen.migrar(self.root, self.clone, BASE)
        (self.root / almacen.LOCAL / 'isbn-1.webp').write_bytes(b'otra')
        self.assertEqual(almacen.verificar(self.root, borrar=True, probe=lambda url, sha: True), (1, []))  # solo isbn-2
        self.assertTrue((self.root / almacen.LOCAL / 'isbn-1.webp').is_file())

    def test_un_nombre_ocupado_en_el_almacen_con_otros_bytes_para_la_migracion(self):
        (self.clone / 'isbn-1.webp').write_bytes(b'distinto')
        with self.assertRaisesRegex(ValueError, 'isbn-1.webp'):
            almacen.migrar(self.root, self.clone, BASE)

    def test_nuevo_abre_el_repo_con_pages_y_deja_la_variable_para_el_final(self):
        calls = []

        def run(cmd, **kw):
            calls.append(cmd)
            if cmd[0] == 'ssh-keygen':
                key = Path(cmd[cmd.index('-f') + 1])
                key.write_text('PRIVADA', encoding='utf-8')
                key.with_suffix('.pub').write_text('PUBLICA', encoding='utf-8')
            return subprocess.CompletedProcess(cmd, 0)
        self.assertEqual(almacen.nuevo(2, run=run), 'https://davidpd89.github.io/web-escritor-portadas-2')
        gh = [c[1:3] for c in calls if c[0] == 'gh']
        self.assertEqual(gh[0], ['repo', 'create'])
        self.assertIn(['api', '--method'], gh)
        self.assertEqual(gh[-1], ['variable', 'set'])  # la carga solo cambia de almacén cuando todo lo demás existe
        self.assertTrue(any(c[0] == 'git' and 'push' in c for c in calls))


class WorkflowAlmacenTest(unittest.TestCase):
    def test_la_carga_abre_el_almacen_de_la_variable_y_no_escribe_en_uno_lleno(self):
        steps = (ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8')
        block = steps[steps.index('Open the cover store'):steps.index('Discover, validate and publish')]
        self.assertIn('vars.READING_COVERS_STORE_REPO', block)
        self.assertIn('almacen_portadas.py cupo', block)
        self.assertIn('READING_COVERS_STORE_URL=', block)
        self.assertLess(block.index('almacen_portadas.py cupo'), block.index('git clone'))


if __name__ == '__main__':
    unittest.main()
