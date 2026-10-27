import unittest
from test_atlas_contract_schema import full, mod


class DuplicateOsmIdentityTest(unittest.TestCase):
    def test_same_osm_object_cannot_be_published_twice(self):
        for osm_type in ('node', 'way', 'relation'):
            with self.subTest(osm_type=osm_type):
                data = full()
                for place in data['places'][:2]:
                    place['osm_type'] = osm_type
                    place['osm_id'] = 123456
                self.assertTrue(
                    mod.problems(data),
                    f'Objeto OSM duplicado aceptado: {osm_type}/123456'
                )

    def test_different_osm_types_may_share_numeric_id(self):
        data = full()
        data['places'][0].update(osm_type='node', osm_id=123456)
        data['places'][1].update(osm_type='way', osm_id=123456)
        self.assertEqual(mod.problems(data), [])


if __name__ == '__main__':
    unittest.main()
