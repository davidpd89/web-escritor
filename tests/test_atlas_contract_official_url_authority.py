import unittest
from test_atlas_contract_schema import full, mod, SCHEMA, Draft202012Validator


@unittest.skipIf(Draft202012Validator is None, 'jsonschema no instalado')
class OfficialUrlAuthorityTest(unittest.TestCase):
    def test_invalid_official_urls_fail_both_layer_contract(self):
        validator = Draft202012Validator(SCHEMA)
        urls = (
            'https:///sin-host',
            'https://user:pass@example.org/perfil',
            'https://example.org:8443/perfil',
            'https://example.org/<script>'
        )
        for section in ('authors', 'places'):
            for url in urls:
                with self.subTest(section=section, url=url):
                    self.assertFalse(mod.valid_https_url(url))
                    data = full()
                    data[section][0]['official_url'] = url
                    errors = list(validator.iter_errors(data))
                    self.assertTrue(
                        errors or mod.problems(data),
                        f'official_url insegura aceptada: {section} {url}'
                    )

    def test_valid_official_urls(self):
        data = full()
        data['authors'][0]['official_url'] = 'https://example.org/autora'
        data['places'][0]['official_url'] = 'https://example.org/libreria'
        self.assertEqual(mod.problems(data), [])
        self.assertEqual(list(Draft202012Validator(SCHEMA).iter_errors(data)), [])


if __name__ == '__main__':
    unittest.main()
