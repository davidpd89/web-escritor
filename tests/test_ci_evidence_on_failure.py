from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ['manecillas-buy-cta-qa.yml', 'manecillas-funnel-qa.yml', 'manecillas-fragments-nav-qa.yml', 'ferias-archive-parity-qa.yml']

class EvidenceRetentionTest(unittest.TestCase):
    def test_browser_workflows_preserve_failure_evidence(self):
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                source = (ROOT / '.github/workflows' / workflow).read_text(encoding='utf-8')
                self.assertRegex(source, r'run:\s*node qa/[^\s]+\.mjs')
                steps = re.split(r'(?m)^      - (?:name:|uses:)', source)
                uploads = [step for step in steps if 'actions/upload-artifact@' in step]
                self.assertTrue(uploads, f'{workflow}: no conserva artefactos')
                self.assertTrue(any('if: always()' in step for step in uploads), f'{workflow}: el upload no se ejecuta tras un fallo')
                self.assertTrue(any('retention-days:' in step for step in uploads), f'{workflow}: retención sin definir')

if __name__ == '__main__':
    unittest.main()