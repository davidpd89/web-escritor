import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_https_boundaries', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class HttpsBoundaries(unittest.TestCase):
    def test_valid_public_url(self):
        self.assertTrue(mod.https('https://example.org/book/123'))

    def test_rejects_unsafe_variants(self):
        urls = [
            'http://example.org/book',
            'https://user:secret@example.org/book',
            'https://example.org:8443/book',
            'https://example.org/book\nInjected: value',
            'https://example.org/book\tvalue',
            'https://example.org/book#bad\rvalue',
            'https://example.org/\x00book',
            'https://example.org/<script>',
            'https://example.org/a b',
            'https://example.org:invalid/book',
        ]
        for url in urls:
            with self.subTest(url=repr(url)):
                self.assertFalse(mod.https(url))

if __name__ == '__main__':
    unittest.main()