"""Cuarentena por libro: un dato malo aparta su libro y el resto del lote sigue validando."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_quarantine as q  # noqa: E402

DATA = json.loads((ROOT / q.CATALOGUE).read_text(encoding='utf-8'))


def without(n):
    """Catálogo sin el libro n y ese libro con sus categorías: así el libro llega como nuevo en la carga."""
    data = copy.deepcopy(DATA)
    book = data['libros'].pop(n)
    cats = sorted(r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == book['id'])
    data['libro_categorias'] = [r for r in data['libro_categorias'] if r['libro_id'] != book['id']]
    return data, book, cats


class QuarantineTest(unittest.TestCase):
    def test_bad_new_book_leaves_the_batch(self):
        before, book, cats = without(0)
        data = copy.deepcopy(DATA)
        data['libros'][0]['autores'] = []
        clean, out = q.isolate(data, ROOT, before, today='2026-11-03')
        self.assertEqual([h['libro']['id'] for h in out], [book['id']])
        self.assertTrue(out[0]['motivo'].startswith(book['id']))
        self.assertEqual(out[0]['categorias'], cats)
        self.assertEqual(clean, before)

    def test_bad_update_keeps_the_published_version(self):
        data = copy.deepcopy(DATA)
        data['libros'][3]['descripcion_breve'] = 'corta'
        clean, out = q.isolate(data, ROOT, DATA)
        self.assertEqual(out[0]['libro']['descripcion_breve'], 'corta')
        self.assertEqual(clean, DATA)

    def test_good_books_are_untouched_and_retried(self):
        data, book, cats = without(1)
        held = [{'libro': book, 'categorias': cats, 'motivo': 'x', 'desde': '2026-10-01'}]
        clean, out = q.isolate(data, ROOT, data, held)
        self.assertEqual(out, [])
        self.assertIn(book, clean['libros'])
        self.assertEqual(q.isolate(DATA, ROOT, DATA), (DATA, []))

    def test_still_bad_held_book_keeps_its_date(self):
        data, book, cats = without(2)
        book['autores'] = []
        held = [{'libro': book, 'categorias': cats, 'motivo': 'x', 'desde': '2026-10-01'}]
        clean, out = q.isolate(data, ROOT, data, held, today='2026-11-03')
        self.assertEqual(clean, data)
        self.assertEqual(out[0]['desde'], '2026-10-01')

    def test_rule_errors_still_stop_the_batch(self):
        data = copy.deepcopy(DATA)
        data['categorias'][0]['tipo'] = 'inventado'
        with self.assertRaises(q.build.ValidationError):
            q.isolate(data, ROOT, DATA)
        broken = copy.deepcopy(DATA)
        broken['libros'][0]['descripcion_breve'] = 'corta'
        with self.assertRaises(q.build.ValidationError):  # publicado y sin cambios: no se despublica en silencio
            q.isolate(broken, ROOT, broken)

    def test_too_many_books_is_a_rule_problem(self):
        data = copy.deepcopy(DATA)
        for b in data['libros'][:q.MAX_BOOKS + 1]:
            b['descripcion_breve'] = 'corta'
        with self.assertRaises(q.build.ValidationError):
            q.isolate(data, ROOT, DATA)

    def test_culprit_is_a_known_book_id(self):
        first = DATA['libros'][0]['id']
        self.assertEqual(q.culprit(f'{first}: falta edicion', DATA), first)
        self.assertEqual(q.culprit(f'{first}.mes: fecha inválida', DATA), first)
        self.assertIsNone(q.culprit('Relación duplicada o referencia inexistente', DATA))


if __name__ == '__main__':
    unittest.main()
