import re
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / 'qa/cls-trace.mjs').read_text(encoding='utf-8')


class CLSErrorAccountingTests(unittest.TestCase):
    def test_navigation_errors_are_not_recorded_as_zero_cls(self):
        catch = re.search(r'catch\s*\(error\)\s*\{(?P<body>.*?)\n\s*\}', SOURCE, re.S)
        self.assertIsNotNone(catch)
        self.assertNotRegex(catch.group('body'), r'total\s*:\s*0\b')

    def test_summary_excludes_failed_navigations(self):
        self.assertRegex(SOURCE, r'rows\.filter\([^\n]*(?:!r\.error|r\.error\s*===\s*undefined)')


if __name__ == '__main__':
    unittest.main()
