import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ('scripts/build-site-shell.py', 'scripts/build-reading-pinterest-rss.py', 'data/reading-catalogue.json', 'package.json', 'package-lock.json')

class LighthouseTransitiveInputs(unittest.TestCase):
    def test_relevant_changes_are_selected(self):
        workflow = (ROOT / '.github/workflows/lighthouse-ci.yml').read_text(encoding='utf-8')
        match = re.search(r'(?s)git diff --name-only.*?grep -qE\s+\x27([^\x27]+)\x27', workflow)
        self.assertIsNotNone(match, 'No se encuentra el selector de cambios')
        pattern = re.compile(match.group(1))
        for path in INPUTS:
            with self.subTest(path=path):
                self.assertIsNotNone(pattern.search(path), f'Lighthouse omite {path}')

if __name__ == '__main__':
    unittest.main()