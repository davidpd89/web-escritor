import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('backfill', ROOT / 'scripts/backfill-reading-metadata.py')
backfill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backfill)
URL = 'https://www.penguinlibros.com/es/libros-ninos-9-anos/37666-libro-coraline-9788498382372'


class FillBookTest(unittest.TestCase):
    def catalogue(self, **book):
        return {'categorias': [], 'libro_categorias': [], 'libros': [{'id': 'lib-0001', **book}]}

    def test_missing_full_synopsis_takes_the_official_one_and_its_source(self):
        cat = self.catalogue(sinopsis_breve='Breve.', sinopsis_tipo='extracto_editorial')
        changes = backfill.fill_book(cat, cat['libros'][0], {'sinopsis_completa': 'Al día siguiente…\n\nSin embargo…'}, URL, '2026-11-02')
        self.assertEqual(cat['libros'][0]['sinopsis_completa'], 'Al día siguiente…\n\nSin embargo…')
        self.assertEqual(cat['libros'][0]['sinopsis_fuente_url'], URL)
        self.assertIn('sinopsis', changes)

    def test_existing_full_synopsis_is_never_replaced(self):
        cat = self.catalogue(sinopsis_completa='Revisada a mano.', sinopsis_fuente_url='https://otra/')
        changes = backfill.fill_book(cat, cat['libros'][0], {'sinopsis_completa': 'Otra.', 'pvp_centimos': 1295}, URL, '2026-11-02')
        self.assertEqual(cat['libros'][0]['sinopsis_completa'], 'Revisada a mano.')
        self.assertEqual(cat['libros'][0]['sinopsis_fuente_url'], 'https://otra/')
        self.assertEqual(changes, {'pvp': 1295})

    def test_own_summary_keeps_its_text_like_the_intake_does(self):
        cat = self.catalogue(sinopsis_breve='Resumen escrito para la web.', sinopsis_tipo='resumen_propio')
        changes = backfill.fill_book(cat, cat['libros'][0], {'sinopsis_completa': 'Oficial.'}, URL, '2026-11-02')
        self.assertNotIn('sinopsis_completa', cat['libros'][0])
        self.assertEqual(changes, {})


if __name__ == '__main__':
    unittest.main()
