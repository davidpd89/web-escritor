import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('press_builder', ROOT / 'scripts/build-press-kit.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
load = lambda p: json.loads((ROOT / p).read_text())

class NumericMutants(unittest.TestCase):
    def test_correlated_invalid_values(self):
        original_book = load('press-kit/las-manecillas-del-recuerdo.json')
        author = load('press-kit/david-porto-diaz.json')
        author['contact']['email'] = 'fixture@example.invalid'
        original_editorial = load('editorial-facts.json')
        manifest = {'assets': [], 'documents': []}
        self.assertEqual(builder.validate(manifest, original_book, author, original_editorial), [])
        mutations = [
            ('pages', True, 'numberOfPages', True),
            ('pages', -1, 'numberOfPages', -1),
            ('priceEUR', -0.01, 'priceEUR', -0.01),
            ('isbn', '9798905149352', 'isbn', '9798905149352')
        ]
        for book_key, book_value, canonical_key, canonical_value in mutations:
            with self.subTest(field=book_key, value=book_value):
                book = copy.deepcopy(original_book)
                editorial = copy.deepcopy(original_editorial)
                book[book_key] = book_value
                editorial['books']['lasManecillasDelRecuerdo'][canonical_key] = canonical_value
                errors = builder.validate(manifest, book, author, editorial)
                self.assertTrue(errors, f'Valor inválido aceptado por consenso entre fuentes: {book_key}={book_value!r}')

if __name__ == '__main__':
    unittest.main()