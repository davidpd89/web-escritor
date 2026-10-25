import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_host_boundary', ROOT / 'scripts/build-sitemap.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CanonicalHostBoundary(unittest.TestCase):
    def test_external_hostname_prefix_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / 'index.html'
            for host in ('davidportodiaz.com.evil.test', 'davidportodiaz.com.example.org'):
                with self.subTest(host=host):
                    url = 'https://' + host + '/articulo/'
                    self.assertIsNone(mod.normalize_canonical(url, root, page))
                    page.write_text('<html><head><link rel="canonical" href="' + url + '"></head></html>', encoding='utf-8')
                    self.assertEqual(mod.collect_urls(root), {})

    def test_official_hostname_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / 'index.html'
            page.write_text('<link rel="canonical" href="https://davidportodiaz.com/">', encoding='utf-8')
            self.assertIn('https://davidportodiaz.com/', mod.collect_urls(root))

if __name__ == '__main__':
    unittest.main()
