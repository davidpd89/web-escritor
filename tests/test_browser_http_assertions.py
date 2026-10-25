import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['manecillas-fragments-nav.mjs', 'manecillas-funnel-browser.mjs', 'manecillas-buy-cta-contract.mjs', 'runtime-scoping-browser.mjs']

class BrowserHTTPAssertions(unittest.TestCase):
    def test_navigations_validate_responses(self):
        for filename in FILES:
            with self.subTest(script=filename):
                source = (ROOT / 'qa' / filename).read_text(encoding='utf-8')
                self.assertRegex(source, r'\.goto\s*\(')
                self.assertRegex(source, r'\.status\s*\(|\.ok\s*\(')

if __name__ == '__main__':
    unittest.main()