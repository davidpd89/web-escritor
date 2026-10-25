import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['manecillas-funnel-qa.yml', 'manecillas-buy-cta-qa.yml', 'runtime-scoping-qa.yml', 'content-parity-manecillas.yml']

class PlaywrightInstallConsistency(unittest.TestCase):
    def test_installation_contract(self):
        for filename in FILES:
            with self.subTest(workflow=filename):
                text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
                self.assertIn('npm ci', text)
                self.assertIn('hashFiles(\'package-lock.json\')', text)
                self.assertIn('playwright install --with-deps chromium', text)
                self.assertIn('playwright install-deps chromium', text)
                self.assertIn("cache-hit == 'true'", text)
                self.assertIn("cache-hit != 'true'", text)

if __name__ == '__main__':
    unittest.main()