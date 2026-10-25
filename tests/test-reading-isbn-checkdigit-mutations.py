import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_isbn_mutations', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class IsbnMutations(unittest.TestCase):
    def test_known_valid_isbn(self):
        self.assertTrue(mod.valid_isbn('9780306406157'))

    def test_every_wrong_check_digit(self):
        original = '9780306406157'
        for digit in '012345689':
            with self.subTest(digit=digit):
                self.assertFalse(mod.valid_isbn(original[:-1] + digit))

    def test_invalid_types_and_shapes(self):
        for value in [None, True, 9780306406157, '978030640615', '97803064061570', '978030640615X', '979 0306406157']:
            with self.subTest(value=repr(value)):
                self.assertFalse(mod.valid_isbn(value))

if __name__ == '__main__':
    unittest.main()