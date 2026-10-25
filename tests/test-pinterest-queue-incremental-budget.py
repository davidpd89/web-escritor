import copy
import importlib.util
import unittest
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pinterest_queue', ROOT / 'scripts/build-reading-pinterest-rss.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class IncrementalQueueTests(unittest.TestCase):
    def test_budget_and_idempotence(self):
        today = date(2026, 10, 25)
        for budget in (1, 2, 3, 5, 20):
            with self.subTest(budget=budget):
                state = {'pins': {}}
                entries = [
                    {'book': {'id': f'lib-{i:04d}', 'slug': f'libro-{i}'}, 'board': {'slug': 'fantasia'}}
                    for i in range(1, 47)
                ]
                self.assertTrue(module.assign_queue(entries[:17], state, today, budget))
                snapshot = copy.deepcopy(state['pins'])
                self.assertFalse(module.assign_queue(entries[:17], state, today, budget))
                self.assertTrue(module.assign_queue(entries, state, today, budget))
                for key, value in snapshot.items():
                    self.assertEqual(state['pins'][key], value)
                counts = Counter(item['scheduled_date'] for item in state['pins'].values())
                self.assertTrue(all(0 < count <= budget for count in counts.values()))
                self.assertEqual(len(state['pins']), len(entries))
                final = copy.deepcopy(state)
                self.assertFalse(module.assign_queue(entries, state, today, budget))
                self.assertEqual(state, final)

if __name__ == '__main__':
    unittest.main()