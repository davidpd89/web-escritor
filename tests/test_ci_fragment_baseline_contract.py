import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('content-parity-manecillas.yml', 'manecillas-fragments-nav-qa.yml')


class FragmentBaselineContract(unittest.TestCase):
    def test_checkout_and_baseline(self):
        for filename in FILES:
            text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
            with self.subTest(filename=filename):
                self.assertIn('fetch-depth: 0', text)
                self.assertIn('github.event.pull_request.base.sha', text)
                self.assertIn('manecillas-fragments-nav.mjs', text)
                self.assertRegex(text, r'BASE_SHA|PR_BASE_SHA')

    def test_missing_historical_file_is_distinguished_from_changed_content(self):
        source = (ROOT / 'qa/manecillas-fragments-nav.mjs').read_text(encoding='utf-8')
        self.assertIn('git', source)
        self.assertIn('cat-file', source)
        self.assertIn('existsInBase', source)
        self.assertIn('deepEqual(afterExcerpts, beforeExcerpts', source)


if __name__ == '__main__':
    unittest.main()