import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['content-parity-manecillas.yml', 'manecillas-fragments-nav-qa.yml']

class CheckoutHistory(unittest.TestCase):
    def test_full_history_available(self):
        for filename in FILES:
            with self.subTest(workflow=filename):
                source = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
                self.assertRegex(source, r'uses:\s*actions/checkout@v\d+')
                self.assertRegex(source, r'fetch-depth:\s*0')

if __name__ == '__main__':
    unittest.main()