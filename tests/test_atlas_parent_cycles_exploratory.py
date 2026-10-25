import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('atlas_cycle_gate', ROOT / 'scripts/atlas_contract_check.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

COLLECTIONS = ('destinations', 'places', 'works', 'authors', 'adaptations', 'sources', 'relationships', 'images', 'routes')


def catalogue(size, cycle):
    data = {'schema_version': 1, **{key: [] for key in COLLECTIONS}}
    for i in range(size):
        item = {'id': f'dst-node-{i:03d}', 'status': 'candidate'}
        if i:
            item['parent_id'] = f'dst-node-{i-1:03d}'
        data['destinations'].append(item)
    if cycle:
        data['destinations'][0]['parent_id'] = f'dst-node-{size-1:03d}'
    return data


class AtlasParentCycles(unittest.TestCase):
    def test_acyclic_chains_are_accepted(self):
        for size in (2, 3, 8, 32):
            with self.subTest(size=size):
                self.assertEqual(mod.problems(catalogue(size, False)), [])

    def test_indirect_cycles_are_rejected(self):
        for size in (2, 3, 8, 32):
            with self.subTest(size=size):
                issues = mod.problems(catalogue(size, True))
                self.assertTrue(issues, f'Ciclo de {size} destinos aceptado')

    def test_cycle_detection_is_independent_of_record_order(self):
        for size in (2, 5, 12):
            data = catalogue(size, True)
            for order in (list(range(size)), list(reversed(range(size)))):
                with self.subTest(size=size, order=order):
                    data['destinations'] = [data['destinations'][i] for i in order]
                    self.assertTrue(mod.problems(data))


if __name__ == '__main__':
    unittest.main()
