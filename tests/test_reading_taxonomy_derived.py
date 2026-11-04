"""Clasificación propia (Romantasy, temporadas, ediciones especiales) derivada de categorías y título."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_taxonomy import apply_derived, derived_categories  # noqa: E402


class DerivedTaxonomyTests(unittest.TestCase):
    def test_romantasy_needs_romance_and_fantasy(self):
        self.assertIn('romantasy', derived_categories({'romance', 'fantasia'}, 'Alas de sangre'))
        self.assertNotIn('romantasy', derived_categories({'romance'}, 'Una boda'))
        self.assertNotIn('romantasy', derived_categories({'fantasia'}, 'El hobbit'))
        # Romantasy también activa San Valentín.
        self.assertIn('san-valentin', derived_categories({'romance', 'fantasia'}, 'X'))

    def test_seasons_from_title_and_triggers(self):
        self.assertIn('halloween', derived_categories(set(), 'La noche de las brujas'))
        self.assertIn('halloween', derived_categories({'terror'}, 'Coraline'))
        self.assertIn('navidad', derived_categories(set(), 'Cuento de Navidad'))
        self.assertEqual(derived_categories({'narrativa'}, 'El camino'), [])

    def test_parenting_book_respects_the_other_parent(self):
        both = derived_categories({'familia-y-crianza'}, 'Educar sin gritos')
        self.assertIn('dia-de-la-madre', both)
        self.assertIn('dia-del-padre', both)
        mother = derived_categories({'familia-y-crianza'}, 'Diario de una madre')
        self.assertIn('dia-de-la-madre', mother)
        self.assertNotIn('dia-del-padre', mother)

    def test_special_editions(self):
        self.assertIn('edicion-especial', derived_categories(set(), 'Dune (edición limitada)'))
        self.assertIn('edicion-especial', derived_categories(set(), 'Alas de hierro: cantos tintados'))
        self.assertNotIn('edicion-especial', derived_categories(set(), 'La edición del siglo'))

    def test_excluded_categories_are_respected(self):
        catalogue = {'categorias': [], 'libro_categorias': [{'libro_id': 'a', 'categoria_id': 'terror'}],
                     'libros': [{'id': 'a', 'titulo': 'Miedo', 'categorias_excluidas': ['halloween']}]}
        self.assertEqual(apply_derived(catalogue), {})
        self.assertEqual({c['id'] for c in catalogue['categorias']} >= {'romantasy', 'halloween'}, True)

    def test_published_catalogue_is_closed_under_derivation(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        trial = copy.deepcopy(catalogue)
        self.assertEqual(apply_derived(trial), {}, 'Ejecuta backfill-reading-metadata.py o apply_derived')
        self.assertEqual(len(trial['categorias']), len(catalogue['categorias']))


if __name__ == '__main__':
    unittest.main()
