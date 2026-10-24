import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('manecillas-buy-cta-qa.yml', 'manecillas-fragments-nav-qa.yml', 'manecillas-funnel-qa.yml', 'runtime-scoping-qa.yml', 'content-parity-manecillas.yml')


class PlaywrightCacheContract(unittest.TestCase):
    def test_cache_key_and_install_branches(self):
        for filename in FILES:
            text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
            with self.subTest(workflow=filename):
                self.assertIn("hashFiles('package-lock.json')", text)
                self.assertRegex(text, r'(?m)^\s*key:.*runner\.os')
                self.assertIn('playwright install --with-deps chromium', text)
                self.assertIn('playwright install-deps chromium', text)
                self.assertIn("cache-hit != 'true'", text)
                self.assertIn("cache-hit == 'true'", text)


if __name__ == '__main__':
    unittest.main()