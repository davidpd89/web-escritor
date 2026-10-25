import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DependencyPinning(unittest.TestCase):
    def test_exact_versions(self):
        package = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
        for section in ['dependencies', 'devDependencies', 'overrides']:
            for name, version in package.get(section, {}).items():
                with self.subTest(package=name):
                    self.assertRegex(version, r'^\d+\.\d+\.\d+$')

    def test_lockfile_matches_manifest(self):
        package = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
        lock = json.loads((ROOT / 'package-lock.json').read_text(encoding='utf-8'))
        root = lock['packages']['']
        for section in ['dependencies', 'devDependencies']:
            self.assertEqual(package.get(section, {}), root.get(section, {}))

if __name__ == '__main__':
    unittest.main()