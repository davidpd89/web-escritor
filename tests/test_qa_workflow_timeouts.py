import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['lighthouse-ci.yml', 'content-parity-manecillas.yml', 'reading-pinterest-rss-qa.yml', 'manecillas-funnel-qa.yml', 'manecillas-buy-cta-qa.yml', 'runtime-scoping-qa.yml', 'manecillas-fragments-nav-qa.yml']

class WorkflowTimeouts(unittest.TestCase):
    def test_jobs_have_bounded_timeout(self):
        for filename in FILES:
            text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
            jobs = text.split('\njobs:', 1)[1]
            blocks = re.split(r'(?m)^  [\w-]+:\s*$', jobs)
            for index, block in enumerate(blocks[1:], 1):
                with self.subTest(workflow=filename, job=index):
                    match = re.search(r'(?m)^    timeout-minutes:\s*(\d+)\s*$', block)
                    self.assertIsNotNone(match)
                    if match:
                        self.assertGreater(int(match.group(1)), 0)
                        self.assertLessEqual(int(match.group(1)), 120)

if __name__ == '__main__':
    unittest.main()