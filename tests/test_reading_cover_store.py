import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_cover_store as store  # noqa: E402

BASE = 'https://davidpd89.github.io/web-escritor-portadas'
CSP = "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self'; img-src 'self' data: c.bing.com; style-src 'self'\">"


def tree(names, local=()):
    directory = tempfile.TemporaryDirectory()
    root = Path(directory.name)
    (root / 'data').mkdir()
    (root / 'data/reading-covers-store.json').write_text(json.dumps({'base_url': BASE, 'archivos': names, 'sha256': {n: store.digest(n.encode()) for n in names}}), encoding='utf-8')
    for name in local:
        (root / 'assets/reading-covers').mkdir(parents=True, exist_ok=True)
        (root / 'assets/reading-covers' / name).write_bytes(b'local')
    return directory, root


class CoverStoreTest(unittest.TestCase):
    def test_the_committed_manifest_is_valid(self):
        # Encendido en la PR #1546 con las fotos de autor: cada nombre, único y con su huella.
        data = store.load(ROOT)
        self.assertTrue(data['base_url'].startswith('https://'))
        self.assertEqual(len(data['archivos']), len(set(data['archivos'])))
        self.assertEqual(set(data['archivos']), set(data['sha256']))

    def test_a_stored_cover_resolves_to_the_store_and_the_rest_stays_on_the_site(self):
        d, root = tree(['isbn-9780000000001.webp'])
        self.addCleanup(d.cleanup)
        self.assertEqual(store.public_url('/assets/reading-covers/isbn-9780000000001.webp', root), BASE + '/isbn-9780000000001.webp')
        self.assertEqual(store.public_url('/assets/reading-covers/otra.webp', root, site='https://x.es'),
                         'https://x.es/assets/reading-covers/otra.webp')

    def test_existence_and_bytes_fall_back_to_the_store(self):
        d, root = tree(['a.webp'], local=['b.webp'])
        self.addCleanup(d.cleanup)
        self.assertTrue(store.exists('/assets/reading-covers/a.webp', root))
        self.assertTrue(store.exists('/assets/reading-covers/b.webp', root))
        self.assertFalse(store.exists('/assets/reading-covers/c.webp', root))
        self.assertEqual(store.read_bytes('/assets/reading-covers/b.webp', root), b'local')
        self.assertEqual(store.read_bytes('/assets/reading-covers/a.webp', root, get=lambda url: url.encode()), (BASE + '/a.webp').encode())
        with self.assertRaises(FileNotFoundError):
            store.read_bytes('/assets/reading-covers/c.webp', root)

    def test_a_bad_manifest_is_refused(self):
        d, root = tree(['../escapa.webp'])
        self.addCleanup(d.cleanup)
        with self.assertRaises(ValueError):
            store.load(root)
        (root / 'data/reading-covers-store.json').write_text(json.dumps({'base_url': 'http://x', 'archivos': ['a.webp']}), encoding='utf-8')
        with self.assertRaises(ValueError):
            store.load(root)

    def test_dist_rewrite_covers_pages_json_and_full_urls_and_only_stored_names(self):
        d, root = tree(['a.webp', 'a-320.webp'])
        self.addCleanup(d.cleanup)
        out = root / 'dist'
        (out / 'x').mkdir(parents=True)
        (out / 'x/index.html').write_text(
            CSP + '<img src="/assets/reading-covers/a.webp" srcset="/assets/reading-covers/a-320.webp 320w, /assets/reading-covers/a.webp 797w">'
            '<img src="/assets/reading-covers/local.webp">', encoding='utf-8')
        (out / 'x/data.json').write_text('{"portada": "https://davidportodiaz.com/assets/reading-covers/a.webp"}', encoding='utf-8')
        (out / 'x/foto.webp').write_bytes(b'\x00\xff binario')
        self.assertEqual(store.apply_to_dist(out, root), 2)
        html = (out / 'x/index.html').read_text(encoding='utf-8')
        self.assertIn(f'src="{BASE}/a.webp"', html)
        self.assertIn(f'{BASE}/a-320.webp 320w', html)
        self.assertIn('src="/assets/reading-covers/local.webp"', html)
        self.assertIn("img-src 'self' data: c.bing.com https://davidpd89.github.io;", html)
        self.assertEqual(json.loads((out / 'x/data.json').read_text(encoding='utf-8'))['portada'], BASE + '/a.webp')
        self.assertEqual((out / 'x/foto.webp').read_bytes(), b'\x00\xff binario')

    def test_an_empty_store_changes_nothing(self):
        d, root = tree([])
        self.addCleanup(d.cleanup)
        out = root / 'dist'
        out.mkdir()
        (out / 'i.html').write_text(CSP + '<img src="/assets/reading-covers/a.webp">', encoding='utf-8')
        self.assertEqual(store.apply_to_dist(out, root), 0)
        self.assertNotIn('github.io', (out / 'i.html').read_text(encoding='utf-8'))


    def test_the_link_check_sees_store_covers_as_the_deploy_publishes_them(self):
        # Lychee lee el checkout, donde las fotos del almacén no existen: sin la reescritura daba «File not found».
        steps = (ROOT / '.github/workflows/broken-links.yml').read_text(encoding='utf-8')
        self.assertIn('python3 scripts/reading_cover_store.py apply .', steps)
        self.assertLess(steps.index('reading_cover_store.py apply'), steps.index('lycheeverse/lychee-action'))


class CoverStoreWriteTest(unittest.TestCase):
    def setUp(self):
        import os
        self.d, self.root = tree([], local=['isbn-9780000000009.webp'])
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.addCleanup(self.dir.cleanup)
        self.saved = os.environ.pop(store.STORE_DIR_ENV, None)
        self.addCleanup(lambda: os.environ.__setitem__(store.STORE_DIR_ENV, self.saved) if self.saved else os.environ.pop(store.STORE_DIR_ENV, None))

    def test_without_a_store_directory_everything_is_written_where_it_always_was(self):
        target = store.put(self.root, '/assets/reading-covers/isbn-9780000000001.webp', b'x')
        self.assertEqual(target, self.root / 'assets/reading-covers/isbn-9780000000001.webp')
        self.assertEqual(store.names(self.root), set())
        self.assertEqual(store.flush(root=self.root), 0)

    def test_with_a_store_directory_new_covers_go_out_and_existing_local_ones_stay(self):
        import os
        os.environ[store.STORE_DIR_ENV] = self.dir.name
        store.put(self.root, '/assets/reading-covers/isbn-9780000000001.webp', b'nueva')
        store.put(self.root, '/assets/reading-covers/isbn-9780000000009.webp', b'cambiada')
        self.assertEqual((Path(self.dir.name) / 'isbn-9780000000001.webp').read_bytes(), b'nueva')
        self.assertFalse((self.root / 'assets/reading-covers/isbn-9780000000001.webp').exists())
        self.assertEqual((self.root / 'assets/reading-covers/isbn-9780000000009.webp').read_bytes(), b'cambiada')
        self.assertEqual(store.names(self.root), {'isbn-9780000000001.webp'})
        self.assertEqual(store.stored_digest('/assets/reading-covers/isbn-9780000000001.webp', self.root), store.digest(b'nueva'))
        # el almacén es de solo añadir: mismos bytes sí, otros bytes nunca (la sustituta lleva nombre nuevo)
        store.put(self.root, '/assets/reading-covers/isbn-9780000000001.webp', b'nueva')
        # otros bytes para un nombre del almacén: no se pisa el almacén ni se para la carga; van al repo
        target = store.put(self.root, '/assets/reading-covers/isbn-9780000000001.webp', b'reemplazo')
        self.assertEqual(target, self.root / 'assets/reading-covers/isbn-9780000000001.webp')
        self.assertEqual(target.read_bytes(), b'reemplazo')
        self.assertEqual((Path(self.dir.name) / 'isbn-9780000000001.webp').read_bytes(), b'nueva')
        self.assertEqual(store.stored_digest('/assets/reading-covers/isbn-9780000000001.webp', self.root), store.digest(b'nueva'))
        self.assertTrue(store.goes_to_store(self.root, '/assets/reading-covers/isbn-9780000000001.webp'))
        self.assertFalse(store.goes_to_store(self.root, '/assets/reading-covers/isbn-9780000000009.webp'))

    def test_a_replacement_gets_a_fresh_name_and_duplicates_are_found_by_digest(self):
        import os
        os.environ[store.STORE_DIR_ENV] = self.dir.name
        first = store.fresh_name('/assets/reading-covers/a.webp', b'uno')
        self.assertRegex(first, r'^/assets/reading-covers/a-v[0-9a-f]{8}\.webp$')
        self.assertEqual(store.fresh_name(first, b'dos').count('-v'), 1)
        store.put(self.root, first, b'uno')
        self.assertEqual(store.owner_of_bytes(b'uno', self.root), first.rsplit('/', 1)[1])
        self.assertIsNone(store.owner_of_bytes(b'uno', self.root, exclude=first))
        self.assertEqual(store.local_file(first, self.root), Path(self.dir.name) / first.rsplit('/', 1)[1])
        self.assertIsNone(store.local_file('/assets/reading-covers/otra.webp', self.root))

    def test_the_manifest_requires_a_digest_for_each_file(self):
        (self.root / store.MANIFEST).write_text(json.dumps({'base_url': BASE, 'archivos': ['a.webp']}), encoding='utf-8')
        with self.assertRaises(ValueError):
            store.load(self.root)

    def test_flush_commits_and_pushes_only_what_changed(self):
        import os
        import subprocess
        remote = tempfile.TemporaryDirectory()
        self.addCleanup(remote.cleanup)
        run = lambda *a, cwd: subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True, text=True)
        run('init', '-q', '--bare', '-b', 'main', cwd=remote.name)
        run('clone', '-q', remote.name, self.dir.name, cwd=remote.name)
        run('config', 'user.name', 't', cwd=self.dir.name)
        run('config', 'user.email', 't@t', cwd=self.dir.name)
        os.environ[store.STORE_DIR_ENV] = self.dir.name
        store.put(self.root, '/assets/reading-covers/isbn-9780000000001.webp', b'nueva')
        self.assertEqual(store.flush(root=self.root), 1)
        self.assertEqual(store.flush(root=self.root), 0)
        self.assertIn('isbn-9780000000001.webp', run('ls-tree', '--name-only', 'main', cwd=remote.name).stdout)
        # lo que una reversión quitó del manifiesto no se sube
        (Path(self.dir.name) / 'huerfana.webp').write_bytes(b'x')
        self.assertEqual(store.flush(root=self.root), 0)
        self.assertNotIn('huerfana.webp', run('ls-tree', '--name-only', 'main', cwd=remote.name).stdout)
        # el almacén rechaza la subida: la carga sigue y la portada vuelve al repo, fuera del manifiesto
        hook = Path(remote.name) / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh' + chr(10) + 'exit 1' + chr(10), encoding='utf-8')
        hook.chmod(0o755)
        store.put(self.root, '/assets/reading-covers/isbn-9780000000002.webp', b'otra')
        self.assertEqual(store.flush(root=self.root), 0)
        self.assertEqual((self.root / 'assets/reading-covers/isbn-9780000000002.webp').read_bytes(), b'otra')
        self.assertEqual(store.names(self.root), {'isbn-9780000000001.webp'})
        self.assertNotIn('isbn-9780000000002.webp', run('ls-tree', '--name-only', 'main', cwd=remote.name).stdout)
        # lo ya subido no se toca y la siguiente subida de la misma carga no arrastra el commit rechazado
        hook.unlink()
        store.put(self.root, '/assets/reading-covers/isbn-9780000000003.webp', b'tercera')
        self.assertEqual(store.flush(root=self.root), 1)
        self.assertEqual(store.names(self.root), {'isbn-9780000000001.webp', 'isbn-9780000000003.webp'})
        # caso 9 de la ronda 2: un nombre sin bytes en origin ni en la copia local es una pérdida real y para
        store.register(self.root, 'fantasma.webp', store.digest(b'nada'))
        with self.assertRaisesRegex(RuntimeError, 'fantasma.webp'):
            store.flush(root=self.root)

    def test_a_store_push_that_clashes_sends_the_covers_back_to_the_repo(self):
        import os
        import subprocess
        remote, other = tempfile.TemporaryDirectory(), tempfile.TemporaryDirectory()
        self.addCleanup(remote.cleanup)
        self.addCleanup(other.cleanup)
        run = lambda *a, cwd: subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True, text=True)
        run('init', '-q', '--bare', '-b', 'main', cwd=remote.name)
        for clone in (self.dir.name, other.name):
            run('clone', '-q', remote.name, clone, cwd=remote.name)
            run('config', 'user.name', 't', cwd=clone)
            run('config', 'user.email', 't@t', cwd=clone)
        os.environ[store.STORE_DIR_ENV] = self.dir.name
        store.put(self.root, '/assets/reading-covers/base.webp', b'base')
        self.assertEqual(store.flush(root=self.root), 1)
        run('pull', '-q', 'origin', 'main', cwd=other.name)
        # otra carga subió el mismo nombre con otros bytes: el rebase choca
        (Path(other.name) / 'isbn-9780000000004.webp').write_bytes(b'ajena')
        run('add', '-A', cwd=other.name)
        run('commit', '-q', '-m', 'x', cwd=other.name)
        run('push', '-q', 'origin', 'HEAD:main', cwd=other.name)
        store.put(self.root, '/assets/reading-covers/isbn-9780000000004.webp', b'propia')
        self.assertEqual(store.flush(root=self.root), 0)
        self.assertEqual((self.root / 'assets/reading-covers/isbn-9780000000004.webp').read_bytes(), b'propia')
        self.assertEqual(store.names(self.root), {'base.webp'})


BASE2 = 'https://otro.github.io/web-escritor-portadas-2'


class VariosAlmacenesTest(unittest.TestCase):
    """Un repositorio de Pages admite 1 GB: lleno el primero, las portadas siguientes van a otro y cada una se sirve
    desde el suyo (25/11, petición de David: «si se llenaba el otro se creaba otro nuevo»)."""

    def setUp(self):
        import os
        self.d, self.root = tree(['a.webp'])
        self.addCleanup(self.d.cleanup)
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        for env in (store.STORE_DIR_ENV, store.STORE_URL_ENV):
            saved = os.environ.pop(env, None)
            self.addCleanup(lambda e=env, v=saved: os.environ.__setitem__(e, v) if v else os.environ.pop(e, None))

    def test_cada_portada_se_sirve_desde_su_almacen_y_la_csp_admite_los_dos(self):
        data = store.load(self.root)
        data['archivos'].append('b.webp')
        data['sha256']['b.webp'] = store.digest(b'b')
        data.update(almacenes=[BASE2], almacen={'b.webp': 1})
        store.write_manifest(self.root, data)
        self.assertEqual(store.public_url('/assets/reading-covers/a.webp', self.root), BASE + '/a.webp')
        self.assertEqual(store.public_url('/assets/reading-covers/b.webp', self.root), BASE2 + '/b.webp')
        text = store.rewrite_text('<img src="/assets/reading-covers/a.webp"><img src="https://davidportodiaz.com/assets/reading-covers/b.webp">', store.load(self.root))
        self.assertEqual(text, f'<img src="{BASE}/a.webp"><img src="{BASE2}/b.webp">')
        csp = store.allow_img_host(CSP, store.load(self.root))
        self.assertIn('https://davidpd89.github.io', csp)
        self.assertIn('https://otro.github.io', csp)

    def test_un_numero_de_almacen_que_no_existe_se_rechaza(self):
        data = store.load(self.root)
        data.update(almacenes=[BASE2], almacen={'a.webp': 2})
        with self.assertRaises(ValueError):
            store.write_manifest(self.root, data)

    def test_la_carga_en_el_almacen_nuevo_registra_alli_y_no_exige_las_del_lleno(self):
        import os
        import subprocess
        remote = tempfile.TemporaryDirectory()
        self.addCleanup(remote.cleanup)
        run = lambda *a, cwd: subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True, text=True)
        run('init', '-q', '--bare', '-b', 'main', cwd=remote.name)
        run('clone', '-q', remote.name, self.dir.name, cwd=remote.name)
        run('config', 'user.name', 't', cwd=self.dir.name)
        run('config', 'user.email', 't@t', cwd=self.dir.name)
        os.environ[store.STORE_DIR_ENV] = self.dir.name
        os.environ[store.STORE_URL_ENV] = BASE2
        store.put(self.root, '/assets/reading-covers/isbn-9780000000001.webp', b'nueva')
        data = store.load(self.root)
        self.assertEqual(data['almacenes'], [BASE2])
        self.assertEqual(data['almacen'], {'isbn-9780000000001.webp': 1})
        self.assertEqual(store.public_url('/assets/reading-covers/isbn-9780000000001.webp', self.root), BASE2 + '/isbn-9780000000001.webp')
        # a.webp vive en el primer almacén: el repo nuevo no la tiene y eso no es una portada 404
        self.assertEqual(store.flush(root=self.root), 1)
        self.assertEqual(run('ls-tree', '--name-only', 'main', cwd=remote.name).stdout.split(), ['isbn-9780000000001.webp'])

    def test_un_manifiesto_de_un_solo_almacen_se_escribe_como_siempre(self):
        store.register(self.root, 'c.webp', store.digest(b'c'))
        raw = json.loads((self.root / store.MANIFEST).read_text(encoding='utf-8'))
        self.assertEqual(set(raw), {'base_url', 'archivos', 'sha256'})


if __name__ == '__main__':
    unittest.main()
