import unittest
from test_atlas_contract_schema import full, mod


class RouteUnlocatedStopsTest(unittest.TestCase):
    def test_unlocated_approved_stop_invalidates_route(self):
        data = full()
        self.assertEqual(mod.problems(data), [])
        data['places'][1]['geo_precision'] = 'unlocated'
        self.assertTrue(
            mod.problems(data),
            'Ruta aprobada conserva una parada sin localización'
        )

    def test_route_with_point_and_city_precision_remains_valid(self):
        data = full()
        self.assertEqual(data['places'][0]['geo_precision'], 'point')
        self.assertEqual(data['places'][1]['geo_precision'], 'city')
        self.assertEqual(mod.problems(data), [])


if __name__ == '__main__':
    unittest.main()
