import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_host', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CanonicalHostBoundary(unittest.TestCase):
    def test_foreign_hosts_are_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / 'index.html'
            page.write_text('<html></html>', encoding='utf-8')
            for url in (
                'https://davidportodiaz.com.evil.example/libro/',
                'https://davidportodiaz.com.attacker.test/',
                'https://davidportodiaz.com@evil.example/',
                'https://davidportodiaz.com:444/libro/',
            ):
                with self.subTest(url=url):
                    self.assertIsNone(module.normalize_canonical(url, root, page))

    def test_legitimate_host_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / 'index.html'
            page.touch()
            self.assertEqual(module.normalize_canonical('https://davidportodiaz.com/', root, page), 'https://davidportodiaz.com/')

if __name__ == '__main__':
    unittest.main()
