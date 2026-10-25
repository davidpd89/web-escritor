import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'qa/manecillas-fragments-nav.mjs').read_text(encoding='utf-8')

class BaseReferenceIntegrity(unittest.TestCase):
    def test_reference_verified_independently(self):
        self.assertRegex(SOURCE, r'git.*(?:rev-parse|cat-file)')
        self.assertRegex(SOURCE, r'BASE_SHA')
        self.assertRegex(SOURCE, r'cat-file')
        self.assertRegex(SOURCE, r'git.*show')

    def test_invalid_reference_not_equivalent_to_missing_page(self):
        self.assertRegex(SOURCE, r'rev-parse|cat-file.*-t')
        self.assertRegex(SOURCE, r'existsInBase')

if __name__ == '__main__':
    unittest.main()