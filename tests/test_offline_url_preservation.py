import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestOfflineURLPreservation(unittest.TestCase):
    def test_navigation_uses_response_not_redirect(self):
        source = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        start = source.index('async function networkFirstPage(')
        end = source.index('async function networkFirstStatic(', start)
        body = source[start:end]
        self.assertIn('staticCache.match("/offline.html")', body)
        self.assertIn('return response', body)
        self.assertNotIn('Response.redirect(', body)
        self.assertNotIn('clients.openWindow(', body)
    def test_retry_uses_current_location(self):
        source = (ROOT / 'offline.html').read_text(encoding='utf-8')
        self.assertIn('window.location.reload()', source)
        self.assertNotIn('window.location.href = "/offline.html"', source)

if __name__ == '__main__':
    unittest.main()