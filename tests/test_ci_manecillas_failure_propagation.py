import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class FailurePropagation(unittest.TestCase):
    def test_qa_steps_are_blocking(self):
        text = (ROOT / '.github/workflows/content-parity-manecillas.yml').read_text(encoding='utf-8')
        names = ('Run content parity QA', 'Re-run fragment preservation/navigation QA', 'Run malformed fragment hash regression')
        for name in names:
            with self.subTest(step=name):
                pattern = r'(?ms)^\s*- name: ' + re.escape(name) + r'\s*\n(.*?)(?=^\s*- name:|\Z)'
                match = re.search(pattern, text)
                self.assertIsNotNone(match)
                step = match.group(1)
                self.assertNotRegex(step, r'continue-on-error:\s*true')
                self.assertNotRegex(step, r'\|\|\s*(?:true|:|echo\b)')
                self.assertNotRegex(step, r'(?m)^\s*if:\s*always\(\)')

if __name__ == '__main__':
    unittest.main()