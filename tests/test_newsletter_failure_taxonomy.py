import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestNewsletterFailures(unittest.TestCase):
    def test_distinct_failure_messages(self):
        src = (ROOT / 'script.js').read_text(encoding='utf-8')
        match = re.search(r'function newsletterErrorMessage\(code\)\s*\{([\s\S]*?)\n\}', src)
        self.assertIsNotNone(match)
        body = match.group(1)
        messages = {}
        for code in ('offline', 'timeout', 'rate_limited'):
            pattern = r'if\s*\(code\s*===\s*[\x22\x27]' + code + r'[\x22\x27]\)\s*return\s*[\x22\x27]([^\x22\x27]+)'
            result = re.search(pattern, body)
            self.assertIsNotNone(result, code)
            messages[code] = result.group(1)
        self.assertEqual(len(set(messages.values())), 3)
    def test_transport_error_classification(self):
        src = (ROOT / 'script.js').read_text(encoding='utf-8')
        self.assertIn('navigator.onLine === false', src)
        self.assertIn('res.status === 429', src)
        self.assertIn('AbortError', src)
        self.assertIn('NEWSLETTER_TIMEOUT_MS', src)

if __name__ == '__main__':
    unittest.main()