import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / '.github/workflows/lighthouse-ci.yml').read_text(encoding='utf-8')

class LighthouseChangeDetection(unittest.TestCase):
    def test_generators_are_relevant(self):
        match = re.search(r"grep -qE '([^']+)'", WORKFLOW)
        self.assertIsNotNone(match)
        pattern = re.compile(match.group(1))
        for path in ['scripts/build-feed.py', 'scripts/build-pagefind-index.py', 'scripts/site_shell.py', 'package-lock.json']:
            with self.subTest(path=path):
                self.assertRegex(path, pattern)

    def test_existing_visual_assets_remain_relevant(self):
        match = re.search(r"grep -qE '([^']+)'", WORKFLOW)
        self.assertIsNotNone(match)
        pattern = re.compile(match.group(1))
        for path in ['assets/v1-book.css', 'libros/index.html', 'script.js', 'lighthouserc.json']:
            with self.subTest(path=path):
                self.assertRegex(path, pattern)

if __name__ == '__main__':
    unittest.main()