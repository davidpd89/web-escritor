import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('content-parity-manecillas.yml', 'lighthouse-ci.yml', 'manecillas-buy-cta-qa.yml', 'manecillas-fragments-nav-qa.yml', 'manecillas-funnel-qa.yml', 'reading-pinterest-rss-qa.yml', 'runtime-scoping-qa.yml')


class TimeoutPermissionsContract(unittest.TestCase):
    def test_all_workflows_are_bounded_and_read_only(self):
        for filename in FILES:
            text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
            with self.subTest(filename=filename):
                values = [int(x) for x in re.findall(r'(?m)^\s*timeout-minutes:\s*(\d+)\s*$', text)]
                self.assertTrue(values, 'Falta timeout')
                self.assertTrue(all(0 < value <= 30 for value in values))
                self.assertRegex(text, r'(?m)^permissions:\s*$')
                self.assertRegex(text, r'(?m)^\s+contents:\s*read\s*$')
                self.assertNotRegex(text, r'(?m)^\s+contents:\s*write\s*$')


if __name__ == '__main__':
    unittest.main()