import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('manecillas-buy-cta-qa.yml', 'manecillas-fragments-nav-qa.yml', 'manecillas-funnel-qa.yml', 'content-parity-manecillas.yml')


class DependencyPathCoverage(unittest.TestCase):
    def test_node_dependency_changes_are_not_silently_skipped(self):
        for filename in FILES:
            text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
            with self.subTest(workflow=filename):
                self.assertIn('npm ci', text)
                trigger = text.split('permissions:', 1)[0]
                self.assertIn('package.json', trigger)
                self.assertIn('package-lock.json', trigger)


if __name__ == '__main__':
    unittest.main()