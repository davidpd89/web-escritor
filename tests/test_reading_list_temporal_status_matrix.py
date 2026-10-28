import copy
import importlib.util
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_list', ROOT / 'scripts/build-reading-list.py')
reading = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reading)

BASE = {'id': 'lectura-prueba', 'title': 'Una lectura', 'author': 'Una autora', 'publish': True, 'note': 'Una observación personal concreta sobre la construcción y la estructura del libro. La nota es suficientemente extensa para esta prueba.', 'status': 'reading', 'started_on': '2026-01-01', 'link_kind': 'none'}

class TemporalStatusMatrix(unittest.TestCase):
    def validate(self, item):
        return reading.validate({'items': [item], 'affiliate_disclosure': ''}, date(2026, 3, 1))

    def test_consistent_states(self):
        for status, finished in [('reading', None), ('paused', None), ('finished', '2026-02-01')]:
            with self.subTest(status=status):
                item = dict(BASE, status=status)
                if finished:
                    item['finished_on'] = finished
                self.assertEqual(len(self.validate(item)[0]), 1)

    def test_inconsistent_states_are_rejected(self):
        cases = [
            {'status': 'reading', 'finished_on': '2026-02-01'},
            {'status': 'paused', 'finished_on': '2026-02-01'},
            {'status': 'finished', 'finished_on': None},
            {'status': 'finished', 'finished_on': '2025-12-31'}
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                item = copy.deepcopy(BASE)
                item.update(changes)
                with self.assertRaises(ValueError):
                    self.validate(item)

if __name__ == '__main__':
    unittest.main()