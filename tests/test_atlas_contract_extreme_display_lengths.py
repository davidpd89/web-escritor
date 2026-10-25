import unittest
from test_atlas_contract_schema import full, mod, SCHEMA, Draft202012Validator


@unittest.skipIf(Draft202012Validator is None, 'jsonschema no instalado')
class ExtremeDisplayLengthsTest(unittest.TestCase):
    def test_extreme_heading_lengths_are_rejected(self):
        fields = (
            ('destinations', 'name'),
            ('places', 'name'),
            ('works', 'title'),
            ('authors', 'name'),
            ('adaptations', 'title'),
            ('routes', 'title')
        )
        validator = Draft202012Validator(SCHEMA)
        for section, field in fields:
            with self.subTest(section=section, field=field):
                data = full()
                data[section][0][field] = 'A' * 2048
                self.assertTrue(
                    list(validator.iter_errors(data)) or mod.problems(data),
                    f'{section}.{field} acepta 2048 caracteres'
                )

    def test_normal_labels_remain_valid(self):
        data = full()
        self.assertEqual(list(Draft202012Validator(SCHEMA).iter_errors(data)), [])
        self.assertEqual(mod.problems(data), [])


if __name__ == '__main__':
    unittest.main()
