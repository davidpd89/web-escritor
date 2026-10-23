from pathlib import Path
from fnmatch import fnmatchcase
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    'content-parity-manecillas.yml': ['editorial-facts.json', 'script.js', 'assets/manecillas-book.js'],
    'manecillas-buy-cta-qa.yml': ['package-lock.json', 'editorial-facts.json'],
    'manecillas-fragments-nav-qa.yml': ['package-lock.json', 'assets/v1-fragments.js'],
    'manecillas-funnel-qa.yml': ['package-lock.json', 'assets/manecillas-funnel.js'],
    'reading-pinterest-rss-qa.yml': ['data/reading-catalogue.json', 'data/reading-pinterest-boards.json']
}

class DependencyTriggerTest(unittest.TestCase):
    def test_dependencies_activate_specialized_jobs(self):
        for workflow, dependencies in CASES.items():
            content = (ROOT / '.github/workflows' / workflow).read_text(encoding='utf-8')
            match = re.search(r'(?m)^  pull_request:\s*\n    paths:\s*\n((?:      - .*\n)+)', content)
            self.assertIsNotNone(match, f'{workflow}: falta declarar paths')
            patterns = re.findall(r"(?m)^      - ['\"]([^'\"]+)['\"]", match.group(1))
            self.assertTrue(patterns, f'{workflow}: lista de rutas vacía')
            for dependency in dependencies:
                with self.subTest(workflow=workflow, dependency=dependency):
                    self.assertTrue(any(fnmatchcase(dependency, pattern) for pattern in patterns), f'{workflow} no se activa al modificar {dependency}')

if __name__ == '__main__':
    unittest.main()