"""Revisión del catálogo con GPT: lo que señala como erróneo, con motivo, sale y no vuelve; nada más cambia."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_taxonomy as tax  # noqa: E402
from test_reading_taxonomy_children import catalogue, cats_of  # noqa: E402
from contrato_libros import incumplen  # noqa: E402

WHY = 'Es un atlas divulgativo de la Biblia, no un libro de humor'


class ReviewTests(unittest.TestCase):
    def data(self):
        data = catalogue(('a', 'Atlas de la Biblia ilustrado', ['humor', 'tema-religion']),
                         ('b', 'Narnia', ['fantasia', 'terror', 'infantil']),
                         ('c', 'Novela', ['narrativa', 'romance']),
                         ('d', 'Sin motivo', ['terror']))
        data['categorias'].append({'id': 'religion-y-espiritualidad', 'slug': 'r', 'nombre': 'r', 'tipo': 'genero',
                                   'orden': 1, 'activa': True})
        for c in data['categorias']:
            c['tipo'] = 'tematica' if c['id'].startswith('tema-') else c['tipo']
        return data

    def opinions(self):
        return {'a': {'generos_gpt': ['religion-y-espiritualidad'], 'sobran': ['humor'], 'motivo': WHY},
                'b': {'generos_gpt': ['fantasia', 'infantil'], 'sobran': ['terror'], 'motivo': 'Fantasía infantil clásica, sin terror'},
                'c': {'generos_gpt': ['romance', 'humor'], 'sobran': [], 'motivo': ''},
                'd': {'generos_gpt': ['humor'], 'sobran': ['terror'], 'motivo': 'corto'}}

    def test_wrong_genre_is_replaced_by_the_main_one(self):
        data, ops = self.data(), self.opinions()
        by_book = {}
        for r in data['libro_categorias']:
            by_book.setdefault(r['libro_id'], set()).add(r['categoria_id'])
        self.assertEqual(tax.apply_review(data, by_book, ops), ['a', 'b'])
        self.assertEqual(cats_of(data, 'a'), {'religion-y-espiritualidad', 'tema-religion'})
        self.assertEqual(cats_of(data, 'b'), {'fantasia', 'infantil'})
        self.assertEqual(cats_of(data, 'c'), {'narrativa', 'romance'})  # sin errores no se añade nada
        self.assertEqual(cats_of(data, 'd'), {'terror'})  # motivo insuficiente
        self.assertEqual(tax.apply_review(data, by_book, ops), [])  # idempotente

    def test_never_leaves_a_book_without_genre(self):
        data = self.data()
        by_book = {'d': {'terror'}}
        ops = {'d': {'generos_gpt': ['terror'], 'sobran': ['terror'], 'motivo': WHY}}
        self.assertEqual(tax.apply_review(data, by_book, ops), [])
        self.assertEqual(cats_of(data, 'd'), {'terror'})

    def test_sheet_books_keep_the_date_the_sheet_gives(self):
        """lib-* sale de la hoja y su fecha también: cambiarla rompe la reimportación (Coraline, 26/11)."""
        data = catalogue(('lib-0001', 'Coraline', ['fantasia', 'misterio-y-thriller']),
                         ('isbn-1', 'Narnia', ['fantasia', 'misterio-y-thriller']))
        for b in data['libros']:
            b['fecha_actualizacion'] = '2026-10-20'
        why = 'Novela de fantasía oscura, no de misterio policiaco'
        ops = {i: {'generos_gpt': ['fantasia'], 'sobran': ['misterio-y-thriller'], 'motivo': why}
               for i in ('lib-0001', 'isbn-1')}
        original = tax.apply_review
        tax.apply_review = lambda c, b, o=None: original(c, b, ops)
        self.addCleanup(setattr, tax, 'apply_review', original)
        tax.repair_classification(data, today='2026-11-26')
        dates = {b['id']: b['fecha_actualizacion'] for b in data['libros']}
        self.assertEqual(dates, {'lib-0001': '2026-10-20', 'isbn-1': '2026-11-26'})
        self.assertNotIn('misterio-y-thriller', cats_of(data, 'lib-0001'))


class PublishedReviewTests(unittest.TestCase):
    def test_flagged_genres_are_gone(self):
        data = json.loads((ROOT / 'data' / 'reading-catalogue.json').read_text(encoding='utf-8'))
        by_book = {}
        for r in data['libro_categorias']:
            by_book.setdefault(r['libro_id'], set()).add(r['categoria_id'])
        genres = {c['id'] for c in data['categorias'] if c['tipo'] == 'genero'}
        malos = {}
        for ident, op in tax.load_opinions(tax.REVIEW_FILE).items():
            if not isinstance(op, dict) or 'generos_gpt' not in op:
                continue
            if unknown := (set(op['generos_gpt']) | set(op.get('sobran') or [])) - genres:
                malos[ident] = 'géneros que no existen: ' + ', '.join(sorted(unknown))
            elif left := tax.review_drop(op, by_book.get(ident, set())):
                if by_book.get(ident, set()) - left & genres:
                    malos[ident] = 'conserva lo que la revisión quita: ' + ', '.join(sorted(left))
        incumplen('la revisión de GPT se aplica: lo que señala como erróneo no se publica', malos)


if __name__ == '__main__':
    unittest.main()
