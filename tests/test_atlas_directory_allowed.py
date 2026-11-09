"""La sincronización del directorio del Atlas publica las páginas de destino que reciben lugares nuevos."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('refresh_atlas_directory', ROOT / 'scripts/refresh-atlas-directory.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AllowedPath(unittest.TestCase):
    def test_destination_pages_hub_sitemap_and_search_index(self):
        # 02/11 y 09/11: falló con atlas-literario/dublin y oxford, que muestran lugares del directorio.
        for path in ('atlas-literario/dublin/index.html', 'atlas-literario/oxford/index.html', 'atlas-literario/index.html',
                     'data/atlas/directory.json', 'sitemap.xml', 'pagefind/fragment/es_1.pf_fragment'):
            with self.subTest(path):
                self.assertTrue(mod.allowed_path(path))

    def test_anything_else_stays_out(self):
        for path in ('index.html', 'atlas-literario/../index.html', 'atlas-literario/dublin/app.js',
                     'data/atlas/catalogue.json', 'scripts/build-atlas-pages.py', 'pagefind/../x'):
            with self.subTest(path):
                self.assertFalse(mod.allowed_path(path))


if __name__ == '__main__':
    unittest.main()
