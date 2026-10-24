import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('content-parity-manecillas.yml', 'lighthouse-ci.yml', 'manecillas-buy-cta-qa.yml', 'manecillas-fragments-nav-qa.yml', 'manecillas-funnel-qa.yml', 'reading-pinterest-rss-qa.yml', 'runtime-scoping-qa.yml')


class ImmutableActionsContract(unittest.TestCase):
    def test_external_actions_are_pinned_by_sha(self):
        for filename in FILES:
            text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
            references = re.findall(r'(?m)^\s*-?\s*uses:\s*([^\s#]+)', text)
            self.assertTrue(references, filename)
            for reference in references:
                if reference.startswith('./'):
                    continue
                with self.subTest(workflow=filename, action=reference):
                    self.assertRegex(reference, r'^[^@]+@[0-9a-f]{40}$')


if __name__ == '__main__':
    unittest.main()