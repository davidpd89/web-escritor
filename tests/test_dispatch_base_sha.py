import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['content-parity-manecillas.yml', 'manecillas-fragments-nav-qa.yml']

class DispatchBaseSHA(unittest.TestCase):
    def test_manual_dispatch_has_fallback(self):
        for filename in FILES:
            with self.subTest(workflow=filename):
                source = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
                self.assertIn('workflow_dispatch:', source)
                self.assertIn('pull_request.base.sha', source)
                self.assertRegex(source, r'github\.event_name.*workflow_dispatch|github\.event\.repository\.default_branch|git merge-base')

if __name__ == '__main__':
    unittest.main()