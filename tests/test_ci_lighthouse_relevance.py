from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/lighthouse-ci.yml'

class LighthouseRelevanceTest(unittest.TestCase):
    def test_selector_includes_actual_page_sources(self):
        source = WORKFLOW.read_text(encoding='utf-8')
        match = re.search(r"grep -qE '([^']+)'", source)
        self.assertIsNotNone(match, 'No se encuentra el selector real de rutas')
        selector = re.compile(match.group(1))
        cases = {
            'index.html': True,
            'assets/v1-book.css': True,
            'script.js': True,
            'scripts/build-site-shell.py': True,
            'scripts/build-reading-pinterest-rss.py': True,
            'data/reading-catalogue.json': True,
            'package.json': True,
            'package-lock.json': True,
            'README.md': False,
            'docs/notes.txt': False
        }
        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                actual = bool(selector.search(filename))
                self.assertEqual(actual, expected, f'Selección incorrecta: {filename}')

if __name__ == '__main__':
    unittest.main()