from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ['content-parity-manecillas.yml', 'manecillas-fragments-nav-qa.yml']

class ManualDispatchBaselineTest(unittest.TestCase):
    def test_manual_dispatch_supplies_a_usable_baseline(self):
        script = (ROOT / 'qa/manecillas-fragments-nav.mjs').read_text(encoding='utf-8')
        self.assertRegex(script, r'assert\(BASE_SHA,')
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                source = (ROOT / '.github/workflows' / workflow).read_text(encoding='utf-8')
                self.assertIn('workflow_dispatch:', source)
                assignment = re.search(r'(?m)^\s*PR_BASE_SHA:\s*(.+)$', source)
                self.assertIsNotNone(assignment)
                expression = assignment.group(1)
                has_fallback = bool(re.search(r'\|\|\s*(?:github\.sha|github\.event\.repository\.default_branch|inputs\.)', expression))
                has_dispatch_guard = bool(re.search(r'if:\s*github\.event_name\s*==\s*[\'\"]pull_request', source))
                self.assertTrue(has_fallback or has_dispatch_guard, f'{workflow}: workflow_dispatch entrega PR_BASE_SHA vacío')

if __name__ == '__main__':
    unittest.main()