import copy
import unittest

from test_atlas_contract_schema import full, mod


class ApprovalTransitionIntegration(unittest.TestCase):
    def test_relationship_dependency_transitions(self):
        cases = (
            ('lugar en revision', 'places', 'lug-libreria'),
            ('obra en revision', 'works', 'obr-a'),
        )
        for label, collection, identifier in cases:
            with self.subTest(case=label):
                data = copy.deepcopy(full())
                entity = next(x for x in data[collection] if x['id'] == identifier)
                entity['status'] = 'reviewed'
                errors = mod.problems(data)
                self.assertTrue(any('relationships/rel-a' in error and 'no aprobado' in error for error in errors), f'{label}: relación aprobada sin dependencia aprobada; errores={errors}')
                data['relationships'][0]['status'] = 'candidate'
                errors = mod.problems(data)
                self.assertFalse(any('relationships/rel-a' in error and 'no aprobado' in error for error in errors), f'{label}: relación candidata bloqueada indebidamente; errores={errors}')


if __name__ == '__main__':
    unittest.main()
