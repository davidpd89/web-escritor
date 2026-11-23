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

    def test_a_parenthesis_without_edition_words_distinguishes_works(self):
        # Revisión Codex de la PR #1546: dos manuales distintos de Javier Rodrigo Agulló se fundían en uno.
        base = 'MP 1782. Nivel básico de Prevención de riesgos laborales'
        books = [{'id': '1', 'titulo': base + ' (Química)'}, {'id': '2', 'titulo': 'La ratonera (Biblioteca Agatha Christie)'},
                 {'id': '3', 'titulo': base + ' (Hostelería y Turismo)'}, {'id': '4', 'titulo': 'La ratonera'},
                 {'id': '5', 'titulo': base}, {'id': '6', 'titulo': 'It (Bolsillo)'}, {'id': '7', 'titulo': 'It'}]
        groups = builder.group_editions(books)
        # Dos materias distintas: dos obras (la sin paréntesis va con la primera). Una colección sola no separa.
        self.assertEqual([(m['id'], [o['id'] for o in rest]) for m, rest in groups], [('1', ['5']), ('2', ['4']), ('3', []), ('6', ['7'])])


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


class AuthorIndexPagesTest(unittest.TestCase):
    """Páginas /recomendaciones/autores/pagina/N/ generadas (revisión Codex de la PR #1546)."""

    def setUp(self):
        import re
        self.re = re
        self.pages = sorted((ROOT / 'recomendaciones/autores/pagina').glob('*/index.html'))
        if not self.pages:
            self.skipTest('índice de autores en una sola página')

    def test_every_page_carries_the_hub_version(self):
        # hydrate() rechaza las continuaciones cuya versión no coincide con la del índice.
        version = lambda path: self.re.search(r'data-catalogue-version="([^"]+)"', path.read_text(encoding='utf-8'))
        hub = version(ROOT / 'recomendaciones/autores/index.html')
        self.assertIsNotNone(hub)
        for page in self.pages:
            found = version(page)
            self.assertIsNotNone(found, page)
            self.assertEqual(found.group(1), hub.group(1), page)

    def test_site_map_links_every_page(self):
        site_map = (ROOT / 'mapa-del-sitio/index.html').read_text(encoding='utf-8')
        for page in self.pages:
            self.assertIn(f'href="/recomendaciones/autores/pagina/{page.parent.name}/"', site_map)


if __name__ == '__main__':
    unittest.main()
