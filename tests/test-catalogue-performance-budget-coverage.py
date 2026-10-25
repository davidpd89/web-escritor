from pathlib import Path
import importlib.util
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check-performance-budgets.py'
SPEC = importlib.util.spec_from_file_location('perf_checker', SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class CataloguePerformanceCoverage(unittest.TestCase):
    def test_catalogue_resources_have_enforced_budget(self):
        html = (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
        manifest = json.loads((ROOT / 'data/performance-budgets.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['enforcement'], 'enforce')
        targets = ['assets/reading-catalogue.js', 'assets/reading-catalogue.css']
        for target in targets:
            self.assertRegex(html, re.escape('/' + target) + r'(?:\?[^\"\']*)?[\"\']')
            self.assertTrue((ROOT / target).is_file(), target)
        covered = set()
        for budget in manifest['budgets']:
            files, errors = MODULE.collect_graph(ROOT, budget['entrypoints'])
            self.assertFalse(errors, (budget['id'], errors))
            covered.update(path.relative_to(ROOT).as_posix() for path in files)
        for target in targets:
            with self.subTest(target=target):
                self.assertIn(target, covered, f'{target} queda fuera de todos los presupuestos')

if __name__ == '__main__':
    unittest.main()