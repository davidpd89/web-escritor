import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class LighthouseLockfileContract(unittest.TestCase):
    def test_lighthouse_uses_locked_dependencies(self):
        workflow = (ROOT / '.github/workflows/lighthouse-ci.yml').read_text(encoding='utf-8')
        package = (ROOT / 'package.json').read_text(encoding='utf-8')
        self.assertIn('"@lhci/cli"', package)
        self.assertRegex(workflow, r'(?m)^\s*run:\s*npm ci\s*$')
        self.assertNotRegex(workflow, r'npm\s+(?:install|i)\s+(?:--global|-g)')
        self.assertRegex(workflow, r'(?:npx\s+--no-install\s+lhci|\./node_modules/\.bin/lhci)\s+(?:collect|assert)')

if __name__ == '__main__':
    unittest.main()