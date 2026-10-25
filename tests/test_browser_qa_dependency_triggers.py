import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['manecillas-funnel-qa.yml', 'manecillas-fragments-nav-qa.yml', 'manecillas-buy-cta-qa.yml', 'content-parity-manecillas.yml']

class DependencyTriggers(unittest.TestCase):
    def test_dependency_changes_trigger_browser_qa(self):
        for filename in FILES:
            with self.subTest(workflow=filename):
                text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
                trigger = text.split('\npermissions:', 1)[0]
                self.assertIn('package.json', trigger)
                self.assertIn('package-lock.json', trigger)

if __name__ == '__main__':
    unittest.main()