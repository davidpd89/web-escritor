import unittest
from test_atlas_contract_schema import full, mod, SCHEMA, Draft202012Validator


@unittest.skipIf(Draft202012Validator is None, 'jsonschema no instalado')
class ImageAltContentTest(unittest.TestCase):
    def test_declared_approved_alt_requires_meaningful_text(self):
        validator = Draft202012Validator(SCHEMA)
        for alt in ('', ' ', '   ', '\t\n'):
            with self.subTest(alt=repr(alt)):
                data = full()
                data['images'][0]['alt_original'] = alt
                self.assertTrue(
                    list(validator.iter_errors(data)) or mod.problems(data),
                    'alt_original vacío aceptado en imagen aprobada'
                )

    def test_meaningful_alt_is_accepted(self):
        data = full()
        data['images'][0]['alt_original'] = 'Entrada de una librería histórica'
        validator = Draft202012Validator(SCHEMA)
        self.assertEqual(list(validator.iter_errors(data)), [])
        self.assertEqual(mod.problems(data), [])


if __name__ == '__main__':
    unittest.main()
