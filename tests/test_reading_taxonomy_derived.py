"""Clasificación propia (Romantasy, ediciones especiales) derivada de categorías y título."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_taxonomy import DERIVED, apply_derived, derived_categories  # noqa: E402


class DerivedTaxonomyTests(unittest.TestCase):
    def test_romantasy_needs_romance_and_fantasy(self):
        self.assertIn('romantasy', derived_categories({'romance', 'fantasia'}, 'Alas de sangre'))
        self.assertNotIn('romantasy', derived_categories({'romance'}, 'Una boda'))
        self.assertNotIn('romantasy', derived_categories({'fantasia'}, 'El hobbit'))

    def test_there_are_no_seasons(self):
        """Sin temporadas en la web (David, 08/11 y 23/11): ni derivadas del género ni del título."""
        for assigned, title in ((set(), 'La noche de las brujas'), ({'terror'}, 'Coraline'), (set(), 'Cuento de Navidad'),
                                ({'romance', 'fantasia'}, 'X'), ({'familia-y-crianza'}, 'Educar sin gritos')):
            self.assertEqual(derived_categories(assigned, title), ['romantasy'] if assigned == {'romance', 'fantasia'} else [])
        self.assertEqual({k for _i, _n, k, *_r in DERIVED}, {'genero', 'contenido'})

    def test_special_editions(self):
        self.assertIn('edicion-especial', derived_categories(set(), 'Dune (edición limitada)'))
        self.assertIn('edicion-especial', derived_categories(set(), 'Alas de hierro: cantos tintados'))
        self.assertNotIn('edicion-especial', derived_categories(set(), 'La edición del siglo'))

    def test_excluded_categories_are_respected(self):
        catalogue = {'categorias': [], 'libro_categorias': [{'libro_id': 'a', 'categoria_id': 'terror'}],
                     'libros': [{'id': 'a', 'titulo': 'Miedo', 'categorias_excluidas': ['romantasy']}]}
        self.assertEqual(apply_derived(catalogue), {})
        self.assertEqual({c['id'] for c in catalogue['categorias']} >= {'romantasy'}, True)

    def test_published_catalogue_is_closed_under_derivation(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        trial = copy.deepcopy(catalogue)
        self.assertEqual(apply_derived(trial), {}, 'Ejecuta backfill-reading-metadata.py o apply_derived')
        self.assertEqual(len(trial['categorias']), len(catalogue['categorias']))


if __name__ == '__main__':
    unittest.main()
