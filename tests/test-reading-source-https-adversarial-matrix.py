import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_https', ROOT / 'scripts/build-reading-catalogue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SourceUrlTests(unittest.TestCase):
    def test_allowed_https_sources(self):
        for url in ('https://example.org/libro', 'https://example.org:443/libro', 'https://editorial.example.org/ficha?isbn=123'):
            with self.subTest(url=url):
                self.assertTrue(module.https(url))

    def test_rejected_sources(self):
        cases = [None, '', 'http://example.org/', 'ftp://example.org/', 'javascript:alert(1)', '//example.org/', 'https://', 'https://user:pass@example.org/', 'https://example.org:444/', 'https://example.org:invalid/', 'https://example.org/\nheader', 'https://example.org/\x00x', 'https://example.org/<script>', 'https://example.org/a b']
        for url in cases:
            with self.subTest(url=repr(url)):
                self.assertFalse(module.https(url))

if __name__ == '__main__':
    unittest.main()