import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['manecillas-fragments-nav.mjs', 'manecillas-funnel-browser.mjs', 'manecillas-buy-cta-contract.mjs', 'runtime-scoping-browser.mjs']

class FixedWaitAudit(unittest.TestCase):
    def test_no_arbitrary_timeouts(self):
        for filename in FILES:
            with self.subTest(script=filename):
                source = (ROOT / 'qa' / filename).read_text(encoding='utf-8')
                waits = re.findall(r'\.waitForTimeout\s*\(\s*\d+\s*\)', source)
                self.assertEqual(waits, [], f'{filename}: sustituir esperas fijas por estados observables: {waits}')

if __name__ == '__main__':
    unittest.main()