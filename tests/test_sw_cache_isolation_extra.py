import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestCacheIsolation(unittest.TestCase):
    def test_activation_is_namespaced(self):
        src = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        start = src.index('self.addEventListener("activate"')
        end = src.index('function isSameOriginGet(', start)
        activation = src[start:end]
        self.assertIn('CURRENT_CACHES.has(key)', activation)
        self.assertIn('LEGACY_PWA_CACHES.has(key)', activation)
        self.assertIn('key.startsWith(`${CACHE_NAMESPACE}-`)', activation)
        self.assertIn('caches.delete(key)', activation)
        self.assertNotIn('caches.delete(STATIC_CACHE)', activation)
        self.assertNotIn('caches.delete(PAGE_CACHE)', activation)

if __name__ == '__main__':
    unittest.main()