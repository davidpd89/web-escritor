import copy
import unittest
from test_atlas_contract_schema import full, mod


class SemanticRelationshipDuplicatesTest(unittest.TestCase):
    def test_identical_approved_relationships_are_rejected(self):
        data = full()
        duplicate = copy.deepcopy(data['relationships'][0])
        duplicate['id'] = 'rel-duplicada'
        data['relationships'].append(duplicate)
        self.assertTrue(
            mod.problems(data),
            'Dos relaciones idénticas con IDs distintos fueron aceptadas'
        )

    def test_distinct_relationship_type_is_not_duplicate(self):
        data = full()
        other = copy.deepcopy(data['relationships'][0])
        other['id'] = 'rel-homenaje'
        other['relationship_type'] = 'literary_homage'
        other['evidence_note'] = 'Homenaje documentado independiente'
        data['relationships'].append(other)
        self.assertEqual(mod.problems(data), [])


if __name__ == '__main__':
    unittest.main()
