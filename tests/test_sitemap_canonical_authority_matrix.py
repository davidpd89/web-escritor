import importlib.util
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap', ROOT / 'scripts/build-sitemap.py')
sitemap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sitemap)

class CanonicalAuthorityMatrix(unittest.TestCase):
    def test_host_boundary_and_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'index.html'
            page.write_text('<html></html>', encoding='utf-8')
            malicious = [
                'https://davidportodiaz.com.evil.example/libro/',
                'https://davidportodiaz.com@evil.example/libro/',
                'https://davidportodiaz.com:444/libro/',
                'https://evil.example/davidportodiaz.com/',
                'https://user:password@davidportodiaz.com/libro/',
                '//davidportodiaz.com.evil.example/libro/'
            ]
            for canonical in malicious:
                with self.subTest(canonical=canonical):
                    result = sitemap.normalize_canonical(canonical, root, page)
                    self.assertTrue(result is None or (urlsplit(result).hostname == 'davidportodiaz.com' and not urlsplit(result).username and not urlsplit(result).password and urlsplit(result).port in (None, 443)), result)
            for canonical in ['https://davidportodiaz.com/libros/', '/libros/']:
                with self.subTest(canonical=canonical):
                    result = sitemap.normalize_canonical(canonical, root, page)
                    self.assertEqual(urlsplit(result).hostname, 'davidportodiaz.com')

if __name__ == '__main__':
    unittest.main()