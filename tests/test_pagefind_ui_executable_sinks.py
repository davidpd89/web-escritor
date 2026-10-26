import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / 'pagefind/pagefind-ui.js'


class TestPagefindExecutableSinks(unittest.TestCase):
    def test_no_dynamic_code_execution(self):
        source = JS.read_text(encoding='utf-8')
        patterns = {
            'eval': r'(?<![\w$.])eval\s*\(',
            'Function constructor': r'\bnew\s+Function\s*\(',
            'document.write': r'\bdocument\s*\.\s*write\s*\(',
            'remote import': r'\bimport\s*\(\s*[\x27\x22]https?://',
        }
        self.assertTrue(source.strip(), 'pagefind/pagefind-ui.js: bundle vacío')
        for name, pattern in patterns.items():
            with self.subTest(sink=name):
                match = re.search(pattern, source)
                self.assertIsNone(match, f'pagefind/pagefind-ui.js: superficie ejecutable {name} en posición {match.start() if match else None}')


if __name__ == '__main__':
    unittest.main()