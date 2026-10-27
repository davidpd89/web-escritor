import importlib.util
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pinterest_budget', ROOT / 'scripts/build-reading-pinterest-rss.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class BudgetTypeTests(unittest.TestCase):
    def test_valid_integer_limits(self):
        for value in (1, 2, 10, 20):
            with self.subTest(value=value):
                state = {'pins': {}}
                module.assign_queue([], state, date(2026, 10, 25), value)
                self.assertEqual(state, {'pins': {}})

    def test_invalid_types_and_bounds(self):
        cases = [None, False, True, 0, -1, 21, 1.0, 2.5, '2', 'abc', [], {}]
        for value in cases:
            with self.subTest(value=repr(value)):
                state = {'pins': {}}
                with self.assertRaises((ValueError, TypeError)):
                    module.assign_queue([], state, date(2026, 10, 25), value)
                self.assertEqual(state, {'pins': {}})

if __name__ == '__main__':
    unittest.main()