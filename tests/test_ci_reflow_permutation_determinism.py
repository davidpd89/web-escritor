import importlib.util
import itertools
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('ci_reflow_selector', ROOT / 'scripts/ci-select-reflow.py')
selector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(selector)

class ReflowPermutationDeterminism(unittest.TestCase):
    def test_selection_is_order_independent(self):
        cases = [
            ['libros/index.html', 'README.md', 'tests/a.py'],
            ['assets/styles.css', 'libros/index.html', 'README.md'],
            ['scripts/build-sitemap.py', 'docs/nota.md', 'sitemap.xml'],
            ['archivo-desconocido.bin', 'libros/index.html', 'README.md'],
        ]
        for files in cases:
            expected_run = selector.classify(files)[0]
            expected_scope = selector.scope_routes(files, exists=lambda _: True)
            for permutation in itertools.permutations(files):
                with self.subTest(files=permutation):
                    self.assertEqual(selector.classify(list(permutation))[0], expected_run)
                    self.assertEqual(selector.scope_routes(list(permutation), exists=lambda _: True), expected_scope)
            duplicated = files + files
            self.assertEqual(selector.classify(duplicated)[0], expected_run)
            self.assertEqual(selector.scope_routes(duplicated, exists=lambda _: True), expected_scope)

if __name__ == '__main__':
    unittest.main()