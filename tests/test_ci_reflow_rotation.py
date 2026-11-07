import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import ci_reflow_rotation as rot  # noqa: E402


def runs(*slots, state='done'):
    return [{'number': 100 - i, 'state': state, 'slot': s} for i, s in enumerate(slots)]


class PickSlot(unittest.TestCase):
    def test_history_of_07_11_fills_the_two_slots_run_number_left_out(self):
        # Runs de main 4113…4092 con run_number % 7: 4, 1, 6, 5, 2, 6, 4 → faltaban 0 y 3.
        history = runs(4, 1, 6, 5, 2, 6, 4)
        self.assertEqual(rot.pick_slot(history, 7), 0)
        self.assertEqual(rot.coverage(history, 7, 0)['faltan'], [0, 3])
        self.assertEqual(rot.pick_slot(runs(0) + history, 7), 3)

    def test_k_runs_in_a_row_cover_every_slot_once(self):
        history = []
        for _ in range(7):
            history.insert(0, {'number': len(history), 'state': 'done', 'slot': rot.pick_slot(history, 7)})
        self.assertEqual(sorted(r['slot'] for r in history), list(range(7)))
        self.assertEqual(rot.coverage(history, 7, 0)['faltan'], [])

    def test_when_all_are_covered_the_oldest_goes_next(self):
        self.assertEqual(rot.pick_slot(runs(3, 0, 1, 2, 4, 5, 6, 3), 7), 6)

    def test_a_running_run_reserves_its_slot(self):
        history = runs(0, state='running') + runs(1, 2, 3, 4, 5, 6)
        self.assertEqual(rot.pick_slot(history, 7), 6)  # la 0 está en curso: la más antigua de las demás
        self.assertEqual(rot.coverage(history, 7, 6)['faltan'], [0])  # en curso no cuenta como cubierta

    def test_runs_without_artifact_are_ignored(self):
        self.assertEqual(rot.pick_slot(runs(None, None, 2), 7), 0)
        self.assertEqual(rot.pick_slot([], 7), 0)


if __name__ == '__main__':
    unittest.main()
