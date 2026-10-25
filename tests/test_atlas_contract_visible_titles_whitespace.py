import unittest
from test_atlas_contract_schema import full, mod, SCHEMA, Draft202012Validator


@unittest.skipIf(Draft202012Validator is None, 'jsonschema no instalado')
class VisibleTitlesWhitespaceTest(unittest.TestCase):
    def test_whitespace_only_public_labels_are_rejected(self):
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
            for value in (' ', '   ', '\n\t'):
                with self.subTest(section=section, field=field, value=repr(value)):
                    data = full()
                    data[section][0][field] = value
                    errors = list(validator.iter_errors(data))
                    self.assertTrue(
                        errors or mod.problems(data),
                        f'{section}.{field} admite texto invisible'
                    )


if __name__ == '__main__':
    unittest.main()
