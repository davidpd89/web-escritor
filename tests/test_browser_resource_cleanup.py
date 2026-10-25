import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['manecillas-fragments-nav.mjs', 'manecillas-funnel-browser.mjs', 'manecillas-buy-cta-contract.mjs', 'runtime-scoping-browser.mjs']

class BrowserCleanup(unittest.TestCase):
    def test_browser_has_protected_cleanup(self):
        for filename in FILES:
            with self.subTest(script=filename):
                source = (ROOT / 'qa' / filename).read_text(encoding='utf-8')
                self.assertRegex(source, r'chromium\.launch\s*\(')
                self.assertRegex(source, r'\bfinally\s*\{')
                self.assertRegex(source, r'\.close\s*\(')

if __name__ == '__main__':
    unittest.main()