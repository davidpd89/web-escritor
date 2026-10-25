import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ('content-parity-manecillas.yml', 'lighthouse-ci.yml', 'reading-pinterest-rss-qa.yml', 'runtime-scoping-qa.yml')

class ReadonlyWorkflowPermissions(unittest.TestCase):
    def test_workflows_use_readonly_token(self):
        for name in WORKFLOWS:
            with self.subTest(workflow=name):
                text = (ROOT / '.github/workflows' / name).read_text(encoding='utf-8')
                self.assertRegex(text, r'(?m)^permissions:\s*\n\s+contents:\s*read\s*$')
                self.assertNotRegex(text, r'(?m)^\s+[\w-]+:\s*write\s*$')

if __name__ == '__main__':
    unittest.main()