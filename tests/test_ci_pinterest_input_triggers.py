import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ('data/reading-catalogue.json', 'data/reading-pinterest-boards.json', 'scripts/build-reading-pinterest-rss.py', 'scripts/export-reading-pinterest-plan.py')

class PinterestInputTriggers(unittest.TestCase):
    def test_all_source_changes_trigger_validation(self):
        text = (ROOT / '.github/workflows/reading-pinterest-rss-qa.yml').read_text(encoding='utf-8')
        trigger = text.split('permissions:', 1)[0]
        for path in REQUIRED:
            with self.subTest(path=path):
                self.assertIn("'" + path + "'", trigger)

if __name__ == '__main__':
    unittest.main()