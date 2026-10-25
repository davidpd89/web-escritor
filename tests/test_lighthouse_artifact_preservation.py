import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / '.github/workflows/lighthouse-ci.yml').read_text(encoding='utf-8')

class ArtifactPreservation(unittest.TestCase):
    def test_local_reports_survive_failure(self):
        section = SOURCE.split('name: Upload local Lighthouse reports', 1)[1]
        self.assertIn('if: always()', section)
        self.assertIn('include-hidden-files: true', section)
        self.assertIn('path: .lighthouseci/', section)
        self.assertRegex(section, r'retention-days:\s*\d+')

    def test_collection_and_assertion_are_separate(self):
        self.assertIn('lhci collect', SOURCE)
        self.assertIn('lhci assert', SOURCE)
        self.assertLess(SOURCE.index('lhci collect'), SOURCE.index('lhci assert'))

if __name__ == '__main__':
    unittest.main()