import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / 'qa/cls-trace.mjs').read_text(encoding='utf-8')


class CLSDiagnosticEvidenceTests(unittest.TestCase):
    def test_layout_shift_evidence_is_preserved(self):
        for token in ('entry.startTime', 'entry.value', 'entry.sources', 's.previousRect', 's.currentRect'):
            with self.subTest(token=token):
                self.assertIn(token, SOURCE)

    def test_font_loading_evidence_is_preserved(self):
        for token in ('document.fonts.status', 'fontsLoaded', 'fontsFinal'):
            with self.subTest(token=token):
                self.assertIn(token, SOURCE)

    def test_diagnostics_are_serialized(self):
        self.assertIn('cls-trace.json', SOURCE)
        self.assertIn('JSON.stringify(report', SOURCE)


if __name__ == '__main__':
    unittest.main()
