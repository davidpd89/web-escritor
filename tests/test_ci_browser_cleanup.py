import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('manecillas-buy-cta-contract.mjs', 'manecillas-funnel-browser.mjs')


class BrowserCleanupTest(unittest.TestCase):
    def test_browser_and_server_cleanup(self):
        for filename in FILES:
            text = (ROOT / 'qa' / filename).read_text(encoding='utf-8')
            with self.subTest(filename=filename):
                self.assertIn('chromium.launch(', text)
                self.assertIn('finally {', text)
                finally_body = text.rsplit('finally {', 1)[1]
                self.assertIn('browser.close()', finally_body)
                self.assertIn('server.close()', finally_body)


if __name__ == '__main__':
    unittest.main()