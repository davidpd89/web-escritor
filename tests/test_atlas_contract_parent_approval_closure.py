import unittest
from test_atlas_contract_schema import full, mod


class ParentApprovalClosureTest(unittest.TestCase):
    def test_approved_child_requires_approved_ancestors(self):
        for state in ('candidate', 'researching', 'rejected', 'retired'):
            with self.subTest(parent_state=state):
                data = full()
                data['destinations'].append({
                    'id': 'dst-region', 'slug': 'region',
                    'name': 'Región sintética', 'country_iso2': 'PT',
                    'status': state
                })
                data['destinations'][0]['parent_id'] = 'dst-region'
                self.assertTrue(
                    mod.problems(data),
                    f'Destino aprobado con padre {state} aceptado'
                )

    def test_approved_parent_is_valid(self):
        data = full()
        data['destinations'][0]['parent_id'] = 'dst-porto'
        self.assertEqual(mod.problems(data), [])


if __name__ == '__main__':
    unittest.main()
