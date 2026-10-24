import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('content-parity-manecillas.yml', 'manecillas-fragments-nav-qa.yml', 'lighthouse-ci.yml')


class ArtifactRetentionContract(unittest.TestCase):
    def test_evidence_survives_failure(self):
        for filename in FILES:
            text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
            with self.subTest(filename=filename):
                blocks = re.split(r'(?m)^\s*- name: ', text)
                uploads = [block for block in blocks if 'actions/upload-artifact@' in block]
                self.assertTrue(uploads, 'Falta subida de evidencias')
                for block in uploads:
                    self.assertIn('always()', block)
                    self.assertRegex(block, r'retention-days:\s*\d+')
                    self.assertNotIn('retention-days: 0', block)


if __name__ == '__main__':
    unittest.main()