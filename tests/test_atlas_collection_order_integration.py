import copy
import unittest

from test_atlas_contract_schema import full, mod


COLLECTIONS = ('destinations', 'places', 'works', 'authors', 'adaptations', 'sources', 'relationships', 'images', 'routes')


class CollectionOrderIntegration(unittest.TestCase):
    def test_reordering_does_not_change_integrity(self):
        baseline = full()
        expected = sorted(mod.problems(baseline))
        self.assertEqual(expected, [], 'Atlas base inválido')
        for collection in COLLECTIONS:
            with self.subTest(collection=collection):
                data = copy.deepcopy(baseline)
                data[collection].reverse()
                actual = sorted(mod.problems(data))
                self.assertEqual(actual, expected, f'{collection}: el orden de registros cambia la validez')

    def test_reordering_preserves_existing_reference_failure(self):
        baseline = full()
        baseline['routes'][0]['place_ids'] = ['lug-libreria', 'lug-oporto']
        expected = sorted(mod.problems(baseline))
        self.assertTrue(any('pertenece a otro destino' in e for e in expected), f'routes/rou-a: error de destino no detectado; errores={expected}')
        for collection in COLLECTIONS:
            with self.subTest(collection=collection):
                data = copy.deepcopy(baseline)
                data[collection].reverse()
                self.assertEqual(sorted(mod.problems(data)), expected, f'{collection}: una reordenación cambia los errores de referencia')


if __name__ == '__main__':
    unittest.main()
