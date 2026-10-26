import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'pagefind/eligible-manifest.json'


class TestManifestSecurity(unittest.TestCase):
    def test_published_paths_are_internal_html(self):
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        pages = manifest['pages']
        self.assertTrue(pages, 'pagefind/eligible-manifest.json: lista de páginas vacía')
        self.assertEqual(manifest['page_count'], len(pages), 'pagefind/eligible-manifest.json: page_count no coincide')
        self.assertEqual(len(pages), len(set(pages)), 'pagefind/eligible-manifest.json: rutas duplicadas')
        for path in pages:
            with self.subTest(path=path):
                self.assertIsInstance(path, str)
                parsed = urlsplit(path)
                self.assertFalse(parsed.scheme or parsed.netloc or parsed.query or parsed.fragment, f'pagefind/eligible-manifest.json: URL no local: {path}')
                self.assertFalse(path.startswith(('/', '\\')), f'pagefind/eligible-manifest.json: ruta absoluta: {path}')
                self.assertNotIn('\\', path, f'pagefind/eligible-manifest.json: separador inesperado: {path}')
                self.assertNotIn('..', Path(path).parts, f'pagefind/eligible-manifest.json: traversal: {path}')
                self.assertTrue(path.endswith('.html'), f'pagefind/eligible-manifest.json: destino no HTML: {path}')
                self.assertTrue((ROOT / path).is_file(), f'pagefind/eligible-manifest.json: archivo inexistente: {path}')


if __name__ == '__main__':
    unittest.main()