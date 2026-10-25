import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXACT = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$')

class DependencyVersionPinning(unittest.TestCase):
    def test_all_direct_dependencies_are_exact(self):
        package = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
        for section in ('dependencies', 'devDependencies', 'optionalDependencies'):
            for name, version in package.get(section, {}).items():
                with self.subTest(section=section, dependency=name):
                    self.assertRegex(version, EXACT, f'{name}: versión no determinista: {version}')

if __name__ == '__main__':
    unittest.main()