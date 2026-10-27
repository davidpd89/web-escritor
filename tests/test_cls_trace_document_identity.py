import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / 'qa/cls-trace.mjs').read_text(encoding='utf-8')


class CLSDocumentIdentityTests(unittest.TestCase):
    def test_http_status_is_checked(self):
        self.assertRegex(SOURCE, r'(response\.ok\(|response\.status\(|\.status\(\)\s*[<>=])')

    def test_final_document_identity_is_checked(self):
        self.assertRegex(SOURCE, r'(page\.url\(\)|document\.location|location\.pathname)')


if __name__ == '__main__':
    unittest.main()
