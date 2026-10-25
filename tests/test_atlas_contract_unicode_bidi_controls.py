import unittest
from test_atlas_contract_schema import full, mod, SCHEMA, Draft202012Validator


@unittest.skipIf(Draft202012Validator is None, 'jsonschema no instalado')
class UnicodeBidiControlsTest(unittest.TestCase):
    def test_bidi_controls_cannot_enter_public_labels(self):
        validator = Draft202012Validator(SCHEMA)
        fields = (
            ('destinations', 'name'),
            ('places', 'name'),
            ('works', 'title'),
            ('authors', 'name'),
            ('routes', 'title')
        )
        for control in (0x202E, 0x202D, 0x2066, 0x2067, 0x2069):
            for section, field in fields:
                with self.subTest(control=hex(control), section=section):
                    data = full()
                    data[section][0][field] = 'Texto ' + chr(control) + 'oculto'
                    self.assertTrue(
                        list(validator.iter_errors(data)) or mod.problems(data),
                        f'Control Unicode {hex(control)} aceptado en {section}.{field}'
                    )


if __name__ == '__main__':
    unittest.main()
