"""Un libro infantil es infantil ante todo: sin terror, romance ni poesía de adultos; sin temporadas; GPT corrige."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_taxonomy as tax  # noqa: E402


def catalogue(*books):
    """books: (id, titulo, categorías)."""
    ids = sorted({c for _i, _t, cats in books for c in cats})
    return {'categorias': [{'id': c, 'slug': c, 'nombre': c, 'tipo': 'genero', 'orden': 1, 'activa': True} for c in ids],
            'libros': [{'id': i, 'titulo': t, 'estado': 'publicado'} for i, t, _c in books],
            'libro_categorias': [{'libro_id': i, 'categoria_id': c} for i, _t, cats in books for c in cats]}


def cats_of(data, book_id):
    return {r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == book_id}


class ChildrenGenreTests(unittest.TestCase):
    def test_infantil_drops_adult_genres(self):
        data = catalogue(('a', 'El lago de los monstruos (INFANTIL)', ['infantil', 'terror']),
                         ('b', 'Los tres cerditos (Pop-up)', ['infantil', 'poesia', 'romance']))
        tax.repair_classification(data)
        self.assertEqual(cats_of(data, 'a'), {'infantil'})
        self.assertEqual(cats_of(data, 'b'), {'infantil'})

    def test_verse_title_keeps_poetry_and_juvenile_keeps_terror(self):
        data = catalogue(('a', 'Poemas para niños', ['infantil', 'poesia']),
                         ('b', 'Noches de miedo', ['infantil', 'juvenil', 'terror']),
                         ('c', 'La casa maldita', ['terror']))
        tax.repair_classification(data)
        self.assertEqual(cats_of(data, 'a'), {'infantil', 'poesia'})
        self.assertEqual(cats_of(data, 'b'), {'infantil', 'juvenil', 'terror'})
        self.assertEqual(cats_of(data, 'c'), {'terror'})

    def test_seasons_are_purged_from_data(self):
        data = catalogue(('a', 'Cuento', ['fantasia', 'halloween']))
        for c in data['categorias']:
            c['tipo'] = 'temporada' if c['id'] == 'halloween' else c['tipo']
        tax.repair_classification(data)
        self.assertNotIn('halloween', cats_of(data, 'a'))
        self.assertFalse([c for c in data['categorias'] if c['tipo'] == 'temporada'])

    def test_infantil_is_the_primary_tag(self):
        order = sorted([{'id': 'terror', 'tipo': 'genero', 'orden': 1}, {'id': 'infantil', 'tipo': 'genero', 'orden': 99}],
                       key=tax.category_priority)
        self.assertEqual(order[0]['id'], 'infantil')

    def test_second_opinion_corrects_audience_and_genre(self):
        data = catalogue(('a', 'Ana y el bosque', ['fantasia']), ('b', 'Dos', ['fantasia', 'infantil']), ('c', 'Tres', ['fantasia']))
        data['categorias'].append({'id': 'infantil', 'slug': 'infantil', 'nombre': 'i', 'tipo': 'genero', 'orden': 1, 'activa': True})
        data['categorias'].append({'id': 'humor', 'slug': 'humor', 'nombre': 'h', 'tipo': 'genero', 'orden': 1, 'activa': True})
        why = 'La sinopsis cuenta una aventura para primeros lectores'
        opinions = {'a': {'genero_gpt': 'Infantil', 'publico_gpt': 'infantil', 'coincide': False, 'motivo': why},
                    'b': {'genero_gpt': 'Humor', 'publico_gpt': 'infantil', 'coincide': True, 'motivo': ''},
                    'c': {'genero_gpt': 'Humor', 'publico_gpt': 'adultos', 'coincide': False, 'motivo': ''}}
        by_book = {'a': {'fantasia'}, 'b': {'fantasia', 'infantil'}, 'c': {'fantasia'}}
        self.assertEqual(tax.apply_second_opinion(data, by_book, opinions), ['a'])  # sin motivo o coincide, nada
        self.assertIn('infantil', cats_of(data, 'a'))
        self.assertNotIn('humor', cats_of(data, 'c'))

    def test_published_catalogue_has_no_adult_genre_on_children_or_seasons(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        by_book = {}
        for r in data['libro_categorias']:
            by_book.setdefault(r['libro_id'], set()).add(r['categoria_id'])
        bad = [(b['id'], sorted(tax.children_drop(b, by_book.get(b['id'], set())))) for b in data['libros']
               if tax.children_drop(b, by_book.get(b['id'], set()))]
        self.assertEqual(bad, [], 'Un libro infantil lleva género de adultos: ejecuta reading_taxonomy.repair_classification')
        self.assertFalse([c['id'] for c in data['categorias'] if c.get('tipo') == 'temporada'])


if __name__ == '__main__':
    unittest.main()
