"""Libros revisados uno a uno (26/11): su clasificación queda fijada en data/reading-classification-verdicts.json.

Origen: las reglas y los nodos de Amazon etiquetaban mal de forma sistemática («aventuras» a toda la fantasía,
«relatos» a novelas, «La gran traición» en terror por la materia «terrorismo»). Ninguna reparación puede deshacer
un veredicto, ni en la primera pasada ni en las siguientes.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_taxonomy as tax  # noqa: E402


def catalogue(rels, ids=('terror', 'narrativa', 'politica-y-actualidad', 'infantil', 'juvenil', 'tema-viajes')):
    kind = {'juvenil': 'edad', 'tema-viajes': 'tematica'}
    return {'categorias': [{'id': c, 'slug': c, 'nombre': c, 'orden': 1, 'activa': True,
                            'tipo': kind.get(c, 'genero')} for c in ids],
            'libros': [{'id': 'isbn-1', 'titulo': 'Libro', 'estado': 'publicado'}],
            'libro_categorias': [{'libro_id': 'isbn-1', 'categoria_id': c} for c in rels]}


def apply(data, verdict):
    by_book = {'isbn-1': {r['categoria_id'] for r in data['libro_categorias']}}
    tax.apply_verdicts(data, by_book, {'isbn-1': verdict})
    return {r['categoria_id'] for r in data['libro_categorias']}


class VerdictLayer(unittest.TestCase):
    def test_replaces_genres_and_keeps_topics(self):
        data = catalogue(['terror', 'tema-viajes'])
        self.assertEqual(apply(data, {'gen': ['politica-y-actualidad'], 'pub': 'a'}),
                         {'politica-y-actualidad', 'tema-viajes'})

    def test_audience(self):
        self.assertEqual(apply(catalogue(['terror']), {'gen': ['narrativa'], 'pub': 'i'}), {'narrativa', 'infantil'})
        self.assertEqual(apply(catalogue(['infantil']), {'gen': ['narrativa'], 'pub': 'j'}), {'narrativa', 'juvenil'})
        self.assertEqual(apply(catalogue(['infantil', 'juvenil']), {'gen': ['narrativa'], 'pub': 'a'}), {'narrativa'})

    def test_romantasy_follows_the_verdict(self):
        data = catalogue(['terror'], ids=('terror', 'romance', 'fantasia', 'romantasy'))
        self.assertEqual(apply(data, {'gen': ['fantasia', 'romance'], 'pub': 'a'}), {'fantasia', 'romance', 'romantasy'})

    def test_creates_new_genre_only_when_used(self):
        data = catalogue(['narrativa'])
        self.assertEqual(apply(data, {'gen': ['teatro'], 'pub': 'a'}), {'teatro'})
        ids = {c['id'] for c in data['categorias']}
        self.assertIn('teatro', ids)
        self.assertNotIn('manuales-y-formacion', ids)

    def test_unknown_genre_never_empties_a_book(self):
        self.assertEqual(apply(catalogue(['terror']), {'gen': ['inventado'], 'pub': 'a'}), {'terror'})


class PublishedCatalogue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        cls.verdicts = tax.load_verdicts()

    def mismatches(self, data):
        genres = {c['id'] for c in data['categorias'] if c['tipo'] == 'genero'}
        by_book = {}
        for rel in data['libro_categorias']:
            by_book.setdefault(rel['libro_id'], set()).add(rel['categoria_id'])
        known = {book['id'] for book in data['libros']}
        wrong = []
        for book_id, verdict in self.verdicts.items():
            if book_id not in known:
                continue  # el libro pudo salir del catálogo; su veredicto no estorba
            want = set(verdict['gen']) | ({tax.CHILD_ID} if verdict['pub'] == 'i' else set())
            if {'romance', 'fantasia'} <= want:
                want.add('romantasy')
            if by_book.get(book_id, set()) & genres - {'fantasia-oscura', 'fantasia-juvenil'} != want & genres:
                wrong.append(book_id)
        return wrong

    def test_published_data_matches_verdicts(self):
        self.assertTrue(self.verdicts)
        self.assertEqual(self.mismatches(self.data)[:10], [])

    def test_repairs_do_not_undo_verdicts(self):
        data = copy.deepcopy(self.data)
        tax.repair_classification(data)
        self.assertEqual(self.mismatches(data)[:10], [])
        self.assertEqual(tax.repair_classification(data), [])


if __name__ == '__main__':
    unittest.main()
