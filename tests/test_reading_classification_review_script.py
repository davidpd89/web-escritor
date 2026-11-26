"""scripts/reading-classification-review.py: lectura de respuestas de GPT y cola de libros por revisar."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_classification_review',
                                              ROOT / 'scripts/reading-classification-review.py')
rev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rev)

CATALOGUE = {
    'categorias': [{'id': 'terror', 'nombre': 'Terror', 'tipo': 'genero'},
                   {'id': 'fantasia-juvenil', 'nombre': 'Fantasía juvenil', 'tipo': 'genero'},
                   {'id': 'infantil', 'nombre': 'Infantil', 'tipo': 'genero'},
                   {'id': 'guias-y-referencia', 'nombre': 'Guías y referencia', 'tipo': 'genero'}],
    'libro_categorias': [{'libro_id': 'narnia', 'categoria_id': 'terror'},
                         {'libro_id': 'narnia', 'categoria_id': 'fantasia-juvenil'},
                         {'libro_id': 'atlas', 'categoria_id': 'terror'}],
    'libros': [{'id': 'narnia', 'titulo': 'El león, la bruja y el armario', 'estado': 'publicado'},
               {'id': 'atlas', 'titulo': 'Atlas de Lovecraft', 'estado': 'publicado'},
               {'id': 'oculto', 'titulo': 'Borrador', 'estado': 'borrador'}],
}


class ReviewScriptTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / 'cat.json'
        path.write_text(json.dumps(CATALOGUE), encoding='utf-8')
        self.cat = rev.Catalogo(path)

    def answer(self, *books):
        return 'Aquí tienes:\n```json\n' + json.dumps({'libros': list(books)}, ensure_ascii=False) + '\n```\nFuentes: ...'

    def test_parse_maps_names_and_keeps_only_current_sobran(self):
        got = rev.parse(self.cat, self.answer(
            {'id': 'narnia', 'generos': ['Fantasía  juvenil', 'Infantil y juvenil'], 'publico': 'Infantil',
             'sobran': ['Terror', 'Guías y referencia'], 'motivo': 'Es fantasía infantil clásica, sin terror.'}))
        self.assertEqual(got['narnia']['generos_gpt'], ['fantasia-juvenil'])  # el nombre fuera de lista se ignora
        self.assertEqual(got['narnia']['sobran'], ['terror'])  # solo lo que el libro tiene
        self.assertEqual(got['narnia']['publico_gpt'], 'infantil')
        self.assertEqual(got['narnia']['genero_nuestro'], ['fantasia-juvenil', 'terror'])

    def test_parse_rejects_unknown_unasked_and_unpublished(self):
        text = self.answer({'id': 'oculto', 'generos': ['Terror'], 'publico': 'adultos'},
                           {'id': 'atlas', 'generos': ['Guías y referencia'], 'publico': 'adultos'},
                           {'id': 'narnia', 'generos': ['Nada'], 'publico': 'adultos'})
        self.assertEqual(set(rev.parse(self.cat, text)), {'atlas'})
        self.assertEqual(rev.parse(self.cat, text, asked={'narnia'}), {})
        self.assertEqual(rev.parse(self.cat, 'sin json'), {})

    def test_correction_without_reason_stays_pending(self):
        """Un «sobran» con motivo corto no se aplicaría: no cuenta como revisado (Codex #1599)."""
        text = self.answer({'id': 'narnia', 'generos': ['Fantasía juvenil'], 'publico': 'infantil',
                            'sobran': ['Terror'], 'motivo': 'no'})
        self.assertEqual(rev.parse(self.cat, text), {})

    def test_pending_returns_book_when_it_gains_an_unseen_genre(self):
        ops = rev.parse(self.cat, self.answer(
            {'id': 'narnia', 'generos': ['Fantasía juvenil'], 'publico': 'infantil', 'sobran': [], 'motivo': ''},
            {'id': 'atlas', 'generos': ['Guías y referencia'], 'publico': 'adultos', 'sobran': [], 'motivo': ''}))
        self.assertEqual(self.cat.pending(ops), [])
        self.cat.by['atlas'].add('infantil')  # la clasificación cambió después de la revisión
        self.assertEqual(self.cat.pending(ops), ['atlas'])

    def test_suspicious_books_go_first(self):
        self.assertGreater(self.cat.score('narnia'), 0)
        self.assertIn('Terror', self.cat.prompt(['narnia']))


if __name__ == '__main__':
    unittest.main()
