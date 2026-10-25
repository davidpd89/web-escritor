import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_timezone', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CalendarTimezoneContract(unittest.TestCase):
    def test_valid_offsets_convert_to_utc(self):
        cases = {
            '2026-06-10T19:00:00+02:00': '20260610T170000Z',
            '2026-01-10T19:00:00+01:00': '20260110T180000Z',
            '2026-06-10T17:00:00Z': '20260610T170000Z',
            '2026-01-01T00:30:00+02:00': '20251231T223000Z',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(module._ical_datetime(value, 'startDate'), expected)

    def test_naive_datetimes_are_rejected(self):
        for value in ('2026-06-10T19:00:00', '2026-06-10T19:00:00.000', '2026-06-10 19:00:00'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    module._ical_datetime(value, 'startDate')

if __name__ == '__main__':
    unittest.main()
