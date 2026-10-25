import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / '.github/workflows/lighthouse-ci.yml').read_text(encoding='utf-8')

class FailureIsolation(unittest.TestCase):
    def test_upload_failure_is_nonblocking(self):
        block = TEXT.split('name: Upload reports to temporary public storage', 1)[1].split('name: Assert budgets', 1)[0]
        self.assertIn('continue-on-error: true', block)

    def test_budget_failure_remains_blocking(self):
        block = TEXT.split('name: Assert budgets', 1)[1].split('name: Upload local Lighthouse reports', 1)[0]
        self.assertIn('lhci assert', block)
        self.assertNotIn('continue-on-error: true', block)
        self.assertNotIn('|| true', block)

if __name__ == '__main__':
    unittest.main()