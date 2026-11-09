import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'rebase_regenerando', Path(__file__).resolve().parents[1] / 'scripts' / 'rebase-regenerando.py')
rr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rr)


class ClasificarTest(unittest.TestCase):
    def test_nuevo_no_generado_no_se_versiona(self):
        cambios, sueltos = rr.clasificar([
            ' M recomendaciones/index.html',
            ' M data/reading-books.json',
            '?? pagefind/fragment/nuevo.pf_fragment',
            '?? reports/performance-budget.json',
        ])
        self.assertEqual(cambios, ['recomendaciones/index.html', 'data/reading-books.json',
                                   'pagefind/fragment/nuevo.pf_fragment'])
        self.assertEqual(sueltos, ['reports/performance-budget.json'])

    def test_generado(self):
        self.assertTrue(rr.generado('sitemap-libros.xml'))
        self.assertTrue(rr.generado('assets/page-order.generated.js'))
        self.assertFalse(rr.generado('data/reading-books.json'))
        self.assertFalse(rr.generado('scripts/build-sitemap.py'))


if __name__ == '__main__':
    unittest.main()
