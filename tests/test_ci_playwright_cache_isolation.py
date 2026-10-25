import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ('content-parity-manecillas.yml', 'runtime-scoping-qa.yml')

class PlaywrightCacheIsolation(unittest.TestCase):
    def test_cache_contract(self):
        for name in WORKFLOWS:
            with self.subTest(workflow=name):
                text = (ROOT / '.github/workflows' / name).read_text(encoding='utf-8')
                self.assertIn("hashFiles('package-lock.json')", text)
                self.assertIn('~/.cache/ms-playwright', text)
                self.assertIn('npx playwright install --with-deps chromium', text)
                self.assertIn('npx playwright install-deps chromium', text)
                self.assertIn("cache-hit == 'true'", text)
                self.assertIn("cache-hit != 'true'", text)

if __name__ == '__main__':
    unittest.main()