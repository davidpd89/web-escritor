"""Filtros del catálogo con número desde el HTML inicial.

Origen: 13/11/2026. «Novela» aparecía sin «(411)» hasta que se tocaba un control, porque el JS solo descarga el
catálogo completo (y recuenta) tras la primera interacción. La build escribe los recuentos de la vista por defecto."""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_catalogue', ROOT / 'scripts/build-reading-catalogue.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def book(i, cat, date, fmt='tapa-blanda'):
    return {'id': i, 'slug': i, 'estado': 'publicado', 'fecha_publicacion': date, 'formato_edicion': fmt, '_cat': cat}


class FacetCountTests(unittest.TestCase):
    def setUp(self):
        self.data = {'categorias': [{'id': 'novela', 'tipo': 'genero', 'nombre': 'Novela'}]}
        self.orig = m.categories, m.book_group, m.public, m.purchase_formats
        m.categories = lambda data, b: [{'id': b['_cat'], 'tipo': 'genero'}]
        m.book_group = lambda cats: 'ficcion'
        m.public = lambda cats: cats
        m.purchase_formats = lambda b: []

    def tearDown(self):
        m.categories, m.book_group, m.public, m.purchase_formats = self.orig

    def test_counts_only_books_already_out_on_the_data_date(self):
        books = [book('a', 'novela', '2026-11-01'), book('b', 'novela', '2026-11-13'),
                 book('c', 'novela', '2026-12-01'), book('d', 'novela', '2026-10-01', 'ebook')]
        counts = m.facet_counts(self.data, books, '2026-11-13')
        self.assertEqual(counts[('genero', 'novela')], 3)
        self.assertEqual(counts[('grupo', 'ficcion')], 3)
        self.assertEqual(counts[('formato', 'tapa-blanda')], 2)
        self.assertEqual(counts[('formato', 'ebook')], 1)

    def test_partial_dates_use_their_first_day(self):
        books = [{'id': 'm', 'fecha_publicacion_parcial': '2026-11', '_cat': 'novela'},
                 {'id': 'y', 'anio_publicacion': 2027, '_cat': 'novela'}]
        self.assertEqual(m.facet_counts(self.data, books, '2026-11-13')[('genero', 'novela')], 1)

    def test_facet_box_prints_the_count(self):
        html = m.facet_group('genero', 'Género', [('novela', 'Novela'), ('poesia', 'Poesía')],
                             counts={('genero', 'novela'): 411})
        self.assertIn('<span>Novela</span><small data-facet-count>(411)</small>', html)
        self.assertIn('<span>Poesía</span><small data-facet-count>(0)</small>', html)


class BuiltHubTests(unittest.TestCase):
    def test_built_hub_has_every_facet_counted(self):
        html = (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
        boxes = re.findall(r'<small data-facet-count>([^<]*)</small>', html)
        self.assertTrue(boxes)
        self.assertEqual([b for b in boxes if not re.fullmatch(r'\(\d+\)', b)], [])


if __name__ == '__main__':
    unittest.main()
