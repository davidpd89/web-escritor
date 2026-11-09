import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('rebase_regenerando', Path(__file__).resolve().parents[1] / 'scripts' / 'rebase-regenerando.py')
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)


class Generado(unittest.TestCase):
    def test_salidas_de_builders(self):
        for p in ('pagefind/fragment/es_1.pf_fragment', 'recomendaciones/index.html', 'recomendaciones/libro/x/index.html',
                  'editoriales/anagrama/index.html', 'sitemap.xml', 'editoriales-sitemap.xml', 'mapa-del-sitio/index.html',
                  'assets/page-order.generated.js'):
            self.assertTrue(rr.generado(p), p)

    def test_codigo_y_datos_no(self):
        for p in ('scripts/build-reading-catalogue.py', 'data/reading-catalogue.json', 'assets/reading-covers/x.webp',
                  'recomendaciones/reading-catalogue.js', 'assets/reading-catalogue.css', 'mapa-del-sitio/otro.html'):
            self.assertFalse(rr.generado(p), p)


if __name__ == '__main__':
    unittest.main()
