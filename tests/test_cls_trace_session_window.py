import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / 'qa/cls-trace.mjs').read_text(encoding='utf-8')


class CLSSessionWindowTests(unittest.TestCase):
    def test_cls_uses_session_windows(self):
        self.assertRegex(SOURCE, r'(sessionWindow|sessionStart|sessionValue|web-vitals)')
        self.assertNotIn('window.__clsTrace.total += entry.value', SOURCE)

    def test_shift_timestamps_are_available(self):
        self.assertIn('entry.startTime', SOURCE)
        self.assertIn('entry.hadRecentInput', SOURCE)


if __name__ == '__main__':
    unittest.main()
