import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))


class DependencyPinningTest(unittest.TestCase):
    def test_all_ci_dependencies_are_exact(self):
        for section in ('dependencies', 'devDependencies', 'overrides'):
            for name, version in DATA.get(section, {}).items():
                with self.subTest(section=section, dependency=name):
                    self.assertIsInstance(version, str)
                    self.assertRegex(version, r'^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$')
                    self.assertNotRegex(version, r'[\^~*><=|]')

    def test_playwright_and_lighthouse_versions_are_pinned(self):
        deps = DATA['devDependencies']
        for name in ('playwright', '@lhci/cli', 'pa11y-ci'):
            self.assertRegex(deps[name], r'^\d+\.\d+\.\d+$')


if __name__ == '__main__':
    unittest.main()