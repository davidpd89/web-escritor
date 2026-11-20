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
    (root / 'data/reading-covers-store.json').write_text(json.dumps({'base_url': BASE, 'archivos': names}), encoding='utf-8')
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


if __name__ == '__main__':
    unittest.main()


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
        self.assertEqual(store.flush(), 0)

    def test_with_a_store_directory_new_covers_go_out_and_existing_local_ones_stay(self):
        import os
        os.environ[store.STORE_DIR_ENV] = self.dir.name
        store.put(self.root, '/assets/reading-covers/isbn-9780000000001.webp', b'nueva')
        store.put(self.root, '/assets/reading-covers/isbn-9780000000009.webp', b'cambiada')
        self.assertEqual((Path(self.dir.name) / 'isbn-9780000000001.webp').read_bytes(), b'nueva')
        self.assertFalse((self.root / 'assets/reading-covers/isbn-9780000000001.webp').exists())
        self.assertEqual((self.root / 'assets/reading-covers/isbn-9780000000009.webp').read_bytes(), b'cambiada')
        self.assertEqual(store.names(self.root), {'isbn-9780000000001.webp'})
        # una portada ya del almacén se actualiza allí aunque exista copia local
        store.put(self.root, '/assets/reading-covers/isbn-9780000000001.webp', b'reemplazo')
        self.assertEqual((Path(self.dir.name) / 'isbn-9780000000001.webp').read_bytes(), b'reemplazo')

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
        self.assertEqual(store.flush(), 1)
        self.assertEqual(store.flush(), 0)
        self.assertIn('isbn-9780000000001.webp', run('ls-tree', '--name-only', 'main', cwd=remote.name).stdout)
