import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
WORKFLOW = (ROOT / '.github/workflows/lighthouse-ci.yml').read_text(encoding='utf-8')


class LighthouseVersionParity(unittest.TestCase):
    def test_global_install_matches_manifest(self):
        match = re.search(r'npm install --global @lhci/cli@([^\s]+)', WORKFLOW)
        self.assertIsNotNone(match, 'No se encuentra la instalación explícita de Lighthouse')
        self.assertEqual(match.group(1), PACKAGE['devDependencies']['@lhci/cli'])

    def test_version_is_not_mobile(self):
        self.assertRegex(PACKAGE['devDependencies']['@lhci/cli'], r'^\d+\.\d+\.\d+$')


if __name__ == '__main__':
    unittest.main()