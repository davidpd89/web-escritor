from pathlib import Path
import importlib.util
import json
import re
import unittest
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check-performance-budgets.py'
SPEC = importlib.util.spec_from_file_location('perf_checker', SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class CataloguePerformanceCoverage(unittest.TestCase):
    def test_raw_catalogue_html_has_a_crawl_limit(self):
        manifest = json.loads((ROOT / 'data/performance-budgets.json').read_text(encoding='utf-8'))
        budget = next(b for b in manifest['budgets'] if b['id'] == 'catalogue-html')
        self.assertEqual(budget['entrypoints'], ['recomendaciones/index.html'])
        self.assertLessEqual(budget['limits']['total_bytes'], 1990000)
        for page in [ROOT / 'recomendaciones/index.html', *ROOT.glob('recomendaciones/pagina/*/index.html')]:
            self.assertLessEqual(MODULE.served_size(page), budget['limits']['total_bytes'], str(page))
        # A real oversized document must fail the production budget checker.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'recomendaciones').mkdir()
            (root / 'recomendaciones/index.html').write_bytes(b'x' * (1990001))
            _, errors = MODULE.evaluate(root, {**manifest, 'budgets': [budget]})
            self.assertTrue(any('total_bytes=' in e and '> limit=' in e for e in errors), errors)

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
