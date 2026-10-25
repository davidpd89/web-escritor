import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class LighthouseEvidenceRetention(unittest.TestCase):
    def test_reports_are_preserved_after_failure(self):
        text = (ROOT / '.github/workflows/lighthouse-ci.yml').read_text(encoding='utf-8')
        match = re.search(r'(?ms)^\s*- name: Upload local Lighthouse reports\s*\n(.*?)(?=^\s*- name:|\Z)', text)
        self.assertIsNotNone(match)
        step = match.group(1)
        self.assertIn('always()', step)
        self.assertIn('steps.changes.outputs.relevant', step)
        self.assertRegex(step, r'include-hidden-files:\s*true')
        self.assertRegex(step, r'if-no-files-found:\s*error')
        self.assertIn('.lighthouseci/', step)

if __name__ == '__main__':
    unittest.main()