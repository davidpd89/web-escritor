import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'build-atlas-literario.py'
spec = importlib.util.spec_from_file_location('atlas_builder_source_url_test', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AtlasSourceURLAdversarial(unittest.TestCase):
    def fixture(self, url):
        return {
            'updated': '2026-10-25',
            'categories': [{'slug': 'literatura', 'name': 'Literatura'}],
            'items': [{
                'slug': 'ruta-literaria',
                'title': 'Ruta literaria',
                'summary': 'Descripción de prueba',
                'category': 'literatura',
                'relationship': 'writer-route',
                'source_urls': [url],
                'status': 'published',
                'verified_date': '2026-10-25',
                'image': {
                    'src': '/assets/atlas-literario-placeholder.webp',
                    'alt': 'Lugar literario',
                    'credit': 'Autor',
                    'license': 'CC BY 4.0',
                    'source_url': 'https://example.org/image'
                }
            }]
        }

    def load_fixture(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'atlas.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            return module.load(path)

    def test_valid_https_sources(self):
        for url in (
            'https://example.org/article',
            'https://example.org:443/article?lang=es',
            'https://biblioteca.example.org/fuente#documento'
        ):
            with self.subTest(url=url):
                data, categories = self.load_fixture(self.fixture(url))
                self.assertEqual(len(data['items']), 1)
                self.assertIn('literatura', categories)

    def test_invalid_https_sources(self):
        invalid = (
            'https://',
            'https:///sin-host',
            'https:// usuario.example.org',
            'https://example.org\nInjected: value',
            'https://user:password@example.org/document',
            'https://example.org:invalid/path',
            'https://example.org:99999/path',
            'https://example.org/<script>',
            'https://example.org/\x00document'
        )
        for url in invalid:
            with self.subTest(url=repr(url)):
                with self.assertRaises(ValueError):
                    self.load_fixture(self.fixture(url))

    def test_every_source_is_validated(self):
        data = self.fixture('https://example.org/valid')
        data['items'][0]['source_urls'].append('https://')
        with self.assertRaises(ValueError):
            self.load_fixture(data)


if __name__ == '__main__':
    unittest.main()
