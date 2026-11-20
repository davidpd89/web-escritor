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
    def test_the_committed_manifest_is_valid_and_empty_until_the_store_is_switched_on(self):
        data = store.load(ROOT)
        self.assertTrue(data['base_url'].startswith('https://'))
        self.assertEqual(data['archivos'], [])

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
        with self.assertRaises(ValueError):
            store.put(self.root, '/assets/reading-covers/isbn-9780000000001.webp', b'reemplazo')
        self.assertEqual((Path(self.dir.name) / 'isbn-9780000000001.webp').read_bytes(), b'nueva')
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
        # un commit que no llegó a subirse se reintenta en la siguiente llamada
        hook = Path(remote.name) / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh' + chr(10) + 'exit 1' + chr(10), encoding='utf-8')
        hook.chmod(0o755)
        store.put(self.root, '/assets/reading-covers/isbn-9780000000002.webp', b'otra')
        with self.assertRaises(RuntimeError):
            store.flush(root=self.root)
        hook.unlink()
        self.assertEqual(store.flush(root=self.root), 1)
        self.assertIn('isbn-9780000000002.webp', run('ls-tree', '--name-only', 'main', cwd=remote.name).stdout)


if __name__ == '__main__':
    unittest.main()
