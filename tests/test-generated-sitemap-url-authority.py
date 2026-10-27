import importlib.util
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_authority', ROOT / 'scripts/build-sitemap.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SitemapAuthority(unittest.TestCase):
    def test_invalid_authorities_are_not_publishable(self):
        page = ROOT / 'index.html'
        cases = [
            'https://usuario:clave@davidportodiaz.com/privado/',
            'https://davidportodiaz.com:8443/privado/',
            'https://davidportodiaz.com@externo.test/',
            'https://davidportodiaz.com.evil.test/',
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertIsNone(mod.normalize_canonical(value, ROOT, page))

    def test_canonical_has_no_fragment_or_tracking_query(self):
        page = ROOT / 'index.html'
        value = 'https://davidportodiaz.com/cuaderno/?utm_source=qa#fragmento'
        result = mod.normalize_canonical(value, ROOT, page)
        self.assertIsNotNone(result)
        parsed = urlsplit(result)
        self.assertEqual(parsed.scheme, 'https')
        self.assertEqual(parsed.hostname, 'davidportodiaz.com')
        self.assertFalse(parsed.username)
        self.assertFalse(parsed.password)
        self.assertFalse(parsed.query)
        self.assertFalse(parsed.fragment)

if __name__ == '__main__':
    unittest.main()
