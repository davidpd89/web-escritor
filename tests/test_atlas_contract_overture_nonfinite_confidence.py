import json
import unittest
from test_atlas_contract_schema import full, mod, SCHEMA, Draft202012Validator


@unittest.skipIf(Draft202012Validator is None, 'jsonschema no instalado')
class OvertureNonfiniteConfidenceTest(unittest.TestCase):
    def test_nonfinite_confidence_is_rejected(self):
        validator = Draft202012Validator(SCHEMA)
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(value=repr(value)):
                data = full()
                data['places'][0]['overture_confidence'] = value
                with self.assertRaises(ValueError):
                    json.dumps(data, allow_nan=False)
                self.assertTrue(
                    list(validator.iter_errors(data)) or mod.problems(data),
                    f'Confianza no finita aceptada: {value!r}'
                )

    def test_finite_extremes_remain_valid(self):
        validator = Draft202012Validator(SCHEMA)
        for value in (0.0, 0.5, 1.0):
            with self.subTest(value=value):
                data = full()
                data['places'][0]['overture_confidence'] = value
                self.assertEqual(list(validator.iter_errors(data)), [])
                self.assertEqual(mod.problems(data), [])
                json.dumps(data, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
