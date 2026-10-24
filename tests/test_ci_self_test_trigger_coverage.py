import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('content-parity-manecillas.yml', 'manecillas-buy-cta-qa.yml', 'manecillas-fragments-nav-qa.yml', 'manecillas-funnel-qa.yml', 'reading-pinterest-rss-qa.yml')


class SelfTestTriggerCoverage(unittest.TestCase):
    def test_executed_tests_are_listed_in_triggers(self):
        for filename in FILES:
            text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
            trigger = text.split('permissions:', 1)[0]
            paths = set(re.findall(r"(?m)^\s*- ['\"]?((?:qa|tests)/[^'\"\s]+\.(?:mjs|py))", trigger))
            executed = set(re.findall(r'\b(?:qa|tests)/[\w.-]+\.(?:mjs|py)', text))
            with self.subTest(filename=filename):
                for path in executed:
                    self.assertIn(path, paths, f'{path} no activa {filename}')


if __name__ == '__main__':
    unittest.main()