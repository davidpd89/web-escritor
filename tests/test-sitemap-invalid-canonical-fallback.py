import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_under_test', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CanonicalFallbackTests(unittest.TestCase):
    def test_invalid_explicit_canonical_never_falls_back(self):
        cases = [
            'javascript:alert(1)',
            'https://example.org/obra/',
            'https://evil.example.org/obra/',
            'ftp://davidportodiaz.com/obra/',
            'https://davidportodiaz.com@evil.example.org/obra/',
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'obra' / 'index.html'
            page.parent.mkdir()
            for canonical in cases:
                with self.subTest(canonical=canonical):
                    page.write_text('<html><head><link rel="canonical" href="' + canonical + '"></head><body><h1>Obra</h1></body></html>', encoding='utf-8')
                    urls = module.collect_urls(root)
                    self.assertEqual(urls, {}, f'Canonical inválido publicado: {canonical}')

if __name__ == '__main__':
    unittest.main()