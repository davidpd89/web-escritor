import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_date_bounds', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ExclusiveCalendarEnd(unittest.TestCase):
    def test_date_boundaries(self):
        cases = [
            ('2026-12-31', None, '20270101'),
            ('2024-02-29', None, '20240301'),
            ('2026-01-30', '2026-02-02', '20260203'),
            ('2026-04-30', None, '20260501'),
        ]
        for start, end, expected in cases:
            with self.subTest(start=start, end=end):
                event = {'startDate': start}
                if end:
                    event['endDate'] = end
                lines = module._event_times(event)
                self.assertEqual(lines[-1], 'DTEND;VALUE=DATE:' + expected)
                self.assertTrue(lines[0].startswith('DTSTART;VALUE=DATE:'))

    def test_reverse_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            module._event_times({'startDate': '2026-05-02', 'endDate': '2026-05-01'})

if __name__ == '__main__':
    unittest.main()
