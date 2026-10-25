import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class LighthouseManualDispatch(unittest.TestCase):
    def test_manual_dispatch_forces_full_audit(self):
        text = (ROOT / '.github/workflows/lighthouse-ci.yml').read_text(encoding='utf-8')
        self.assertRegex(text, r'(?m)^\s+workflow_dispatch:\s*$')
        selector = re.search(r'(?s)- name: Detect relevant changes(.*?)(?=\n\s+- name:|\Z)', text)
        self.assertIsNotNone(selector)
        step = selector.group(1)
        guard = step.find('github.event_name')
        forced = step.find('relevant=true')
        diff = step.find('git diff --name-only')
        self.assertGreaterEqual(guard, 0)
        self.assertGreater(forced, guard)
        self.assertGreater(diff, forced)
        self.assertRegex(step, r'if\s+\[.*github\.event_name.*!=.*pull_request.*\]')

if __name__ == '__main__':
    unittest.main()