import copy
import importlib.util
import itertools
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('topic_builder_order', ROOT / 'scripts/build-topic-collections.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASE = json.loads((ROOT / 'data/topic-collections.json').read_text(encoding='utf-8'))

class PublicationOrder(unittest.TestCase):
    def test_permutation_preserves_publication_set(self):
        records = BASE['collections']
        expected = {r['slug'] for r in records if r['status'] == 'ready'}
        self.assertTrue(expected)
        self.assertTrue(any(r['status'] == 'draft' for r in records))
        for permutation in itertools.permutations(records):
            with self.subTest(order=[r['slug'] for r in permutation]):
                payload = copy.deepcopy(BASE)
                payload['collections'] = list(copy.deepcopy(permutation))
                validated = MODULE.validate(payload)
                actual = {r['slug'] for r in validated if r['status'] == 'ready'}
                self.assertEqual(actual, expected)
                self.assertTrue(actual.isdisjoint({r['slug'] for r in validated if r['status'] == 'draft'}))

    def test_ready_requires_three_distinct_items(self):
        for index in range(3):
            payload = copy.deepcopy(BASE)
            ready = next(r for r in payload['collections'] if r['status'] == 'ready')
            ready['items'].pop(index)
            with self.subTest(removed=index):
                with self.assertRaises(MODULE.ValidationError):
                    MODULE.validate(payload)

if __name__ == '__main__':
    unittest.main()
