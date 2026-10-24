import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / '.github/workflows/lighthouse-ci.yml').read_text(encoding='utf-8')


def relevant(path):
    pattern = r'\.(html|css|js)$|^assets/|^manifest\.json$|^service-worker\.js$|^lighthouserc\.json$|^\.github/workflows/lighthouse-ci\.yml$'
    return bool(re.search(pattern, path))


class LighthouseTriggerTest(unittest.TestCase):
    def test_dependency_changes_trigger_audit(self):
        for path in ('package.json', 'package-lock.json', 'lighthouserc.json'):
            with self.subTest(path=path):
                self.assertTrue(relevant(path), f'Lighthouse omitido para {path}')

    def test_actual_selector_contains_dependency_paths(self):
        for path in ('package.json', 'package-lock.json'):
            self.assertIn(path, TEXT, f'El selector no contempla {path}')


if __name__ == '__main__':
    unittest.main()