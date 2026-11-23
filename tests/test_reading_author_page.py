"""Ficha de autor: ediciones de una misma obra agrupadas y autores parecidos solo por géneros (auditoría 23/11)."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("builder_author_page", ROOT / "scripts/build-reading-catalogue.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def cat(cid, tipo='genero'):
    return {'id': cid, 'nombre': cid.title(), 'tipo': tipo, 'activa': True, 'orden': 0}


class EditionGroupingTest(unittest.TestCase):
    def test_special_editions_join_the_same_work(self):
        books = [{'id': '2', 'titulo': 'Dioses del juego 3. The Keeper (Edición especial)'},
                 {'id': '1', 'titulo': 'Dioses del juego 3. The Keeper'},
                 {'id': '3', 'titulo': 'It: Edición limitada a precio especial'},
                 {'id': '4', 'titulo': 'It'},
                 {'id': '5', 'titulo': 'Carrie'}]
        groups = builder.group_editions(books)
        self.assertEqual([(m['id'], [o['id'] for o in rest]) for m, rest in groups], [('2', ['1']), ('3', ['4']), ('5', [])])

    def test_different_works_stay_apart(self):
        self.assertNotEqual(builder.edition_key('El resplandor'), builder.edition_key('Doctor Sueño'))


class SimilarAuthorsTest(unittest.TestCase):
    def setUp(self):
        cats = [cat('terror'), cat('narrativa'), cat('romance'), cat('adultos', 'edad')]
        links = {'a': ['terror', 'narrativa', 'adultos'], 'b': ['terror', 'adultos'], 'c': ['narrativa', 'adultos'],
                 'd': ['romance', 'narrativa'], 'e': ['narrativa'], 'f': ['terror']}
        self.data = {'categorias': cats, 'libro_categorias': [{'libro_id': b, 'categoria_id': c} for b, cs in links.items() for c in cs]}
        self.books = [{'id': 'a', 'autores': ['King']}, {'id': 'b', 'autores': ['Straub']}, {'id': 'c', 'autores': ['Común']},
                      {'id': 'd', 'autores': ['Romántica']}, {'id': 'e', 'autores': ['Otra']}, {'id': 'f', 'autores': ['Varios autores']}]
        self.authors = [{'nombre': n} for n in ('King', 'Straub', 'Común', 'Romántica', 'Otra', 'Varios autores')]

    def test_rare_genre_weighs_more_and_collectives_are_left_out(self):
        names = [o['nombre'] for o in builder.similar_authors({'nombre': 'King'}, self.data, self.books, self.authors)]
        self.assertEqual(names[0], 'Straub')  # comparte «terror», menos frecuente que «narrativa»
        self.assertNotIn('Varios autores', names)
        self.assertNotIn('King', names)

    def test_age_alone_never_relates(self):
        names = [o['nombre'] for o in builder.similar_authors({'nombre': 'Romántica'}, self.data, self.books, self.authors)]
        self.assertNotIn('Straub', names)  # solo comparten la edad, que no cuenta


if __name__ == '__main__':
    unittest.main()
