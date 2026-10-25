import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class BrowserFixedSleepAudit(unittest.TestCase):
    def test_no_arbitrary_sleep(self):
        text = (ROOT / 'qa/manecillas-cross-engine.mjs').read_text(encoding='utf-8')
        self.assertNotRegex(text, r'\b(?:waitForTimeout|setTimeout|setInterval)\s*\(')
        self.assertIn('document.fonts', text)
        self.assertIn('setViewportSize', text)

if __name__ == '__main__':
    unittest.main()