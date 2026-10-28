import unittest
from test_atlas_contract_schema import full, mod


class EvidenceCausalDatesTest(unittest.TestCase):
    def test_approval_cannot_precede_source_retrieval(self):
        for section in ('places', 'relationships'):
            with self.subTest(section=section):
                data = full()
                data['sources'][0]['retrieved_at'] = '2026-10-21'
                data[section][0]['verified_at'] = '2026-10-20'
                self.assertTrue(
                    mod.problems(data),
                    f'{section}: aprobación anterior a evidencia aceptada'
                )

    def test_same_day_evidence_and_verification(self):
        self.assertEqual(mod.problems(full()), [])


if __name__ == '__main__':
    unittest.main()
