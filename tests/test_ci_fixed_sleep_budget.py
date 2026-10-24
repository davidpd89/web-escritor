import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('manecillas-buy-cta-contract.mjs', 'manecillas-funnel-browser.mjs', 'manecillas-fragments-nav.mjs')


class FixedSleepBudget(unittest.TestCase):
    def test_no_long_fixed_waits(self):
        for filename in FILES:
            text = (ROOT / 'qa' / filename).read_text(encoding='utf-8')
            values = [int(value) for value in re.findall(r'waitForTimeout\(\s*(\d+)\s*\)', text)]
            with self.subTest(filename=filename):
                self.assertTrue(all(value <= 2000 for value in values), f'Esperas excesivas: {values}')
                self.assertLessEqual(sum(values), 15000, f'Presupuesto de esperas excesivo: {sum(values)} ms')


if __name__ == '__main__':
    unittest.main()