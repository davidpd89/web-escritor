import unittest
from test_atlas_contract_schema import full, mod, SCHEMA, Draft202012Validator


@unittest.skipIf(Draft202012Validator is None, 'jsonschema no instalado')
class GeographicExactBoundariesTest(unittest.TestCase):
    def test_exact_valid_boundaries(self):
        validator = Draft202012Validator(SCHEMA)
        for latitude, longitude in ((-90, -180), (-90, 180), (90, -180), (90, 180), (0, 0)):
            with self.subTest(latitude=latitude, longitude=longitude):
                data = full()
                data['places'][0].update(latitude=latitude, longitude=longitude)
                self.assertEqual(list(validator.iter_errors(data)), [])
                self.assertEqual(mod.problems(data), [])

    def test_immediately_outside_boundaries(self):
        validator = Draft202012Validator(SCHEMA)
        cases = ((-90.000001, 0), (90.000001, 0), (0, -180.000001), (0, 180.000001))
        for latitude, longitude in cases:
            with self.subTest(latitude=latitude, longitude=longitude):
                data = full()
                data['places'][0].update(latitude=latitude, longitude=longitude)
                self.assertTrue(list(validator.iter_errors(data)))
                self.assertTrue(mod.problems(data))

    def test_boolean_coordinates_are_not_numbers(self):
        validator = Draft202012Validator(SCHEMA)
        for field in ('latitude', 'longitude'):
            with self.subTest(field=field):
                data = full()
                data['places'][0][field] = True
                self.assertTrue(list(validator.iter_errors(data)))
                self.assertTrue(mod.problems(data))


if __name__ == '__main__':
    unittest.main()
