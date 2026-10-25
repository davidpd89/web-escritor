import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ManecillasHTTPNavigation(unittest.TestCase):
    def test_each_navigation_checks_http_response(self):
        text = (ROOT / 'qa/manecillas-cross-engine.mjs').read_text(encoding='utf-8')
        matches = list(re.finditer(r'\b(?:const|let)?\s*\w+\s*=\s*await\s+page\.goto\(|\b\w+\s*=\s*await\s+page\.goto\(', text))
        self.assertGreaterEqual(len(matches), 2)
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section = text[match.end():end]
            self.assertRegex(section, r'\.ok\(\)|\.status\(\)', f'Navegación {index + 1} sin comprobación HTTP')

if __name__ == '__main__':
    unittest.main()