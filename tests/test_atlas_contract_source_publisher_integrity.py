import unittest
from test_atlas_contract_schema import full, mod, SCHEMA, Draft202012Validator


@unittest.skipIf(Draft202012Validator is None, 'jsonschema no instalado')
class SourcePublisherIntegrityTest(unittest.TestCase):
    def test_approved_evidence_requires_nonblank_publisher(self):
        validator = Draft202012Validator(SCHEMA)
        for publisher in (' ', '   ', '\t\n'):
            with self.subTest(publisher=repr(publisher)):
                data = full()
                data['sources'][0]['publisher'] = publisher
                self.assertTrue(
                    list(validator.iter_errors(data)) or mod.problems(data),
                    'Fuente aprobada con publicador invisible aceptada'
                )

    def test_identified_publisher_is_valid(self):
        data = full()
        data['sources'][0]['publisher'] = 'Archivo cultural de prueba'
        self.assertEqual(mod.problems(data), [])
        self.assertEqual(list(Draft202012Validator(SCHEMA).iter_errors(data)), [])


if __name__ == '__main__':
    unittest.main()
