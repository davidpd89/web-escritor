import unittest
from test_atlas_contract_schema import full, mod


class AtlasParentCyclesTest(unittest.TestCase):
    def test_cycles_of_multiple_lengths_are_rejected(self):
        self.assertEqual(mod.problems(full()), [])
        for size in (2, 3, 5):
            with self.subTest(size=size):
                data = full()
                ids = ['dst-lisboa', 'dst-porto']
                for i in range(2, size):
                    eid = f'dst-extra-{i}'
                    ids.append(eid)
                    data['destinations'].append({
                        'id': eid, 'status': 'approved',
                        'verified_at': '2026-10-21',
                        'slug': f'extra-{i}', 'name': f'Región {i}',
                        'country_iso2': 'PT'
                    })
                index = {x['id']: x for x in data['destinations']}
                for pos, eid in enumerate(ids):
                    index[eid]['parent_id'] = ids[(pos + 1) % size]
                issues = mod.problems(data)
                self.assertTrue(issues, f'Ciclo de {size} destinos aceptado')


if __name__ == '__main__':
    unittest.main()
