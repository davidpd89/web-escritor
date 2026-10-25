import importlib.util
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_boundary', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CalendarLocalDateBoundary(unittest.TestCase):
    def test_all_day_event_remains_available_until_local_midnight(self):
        event = {'startDate': '2030-06-10', 'endDate': '2030-06-10'}
        madrid = timezone(timedelta(hours=2))
        before_midnight = datetime(2030, 6, 10, 23, 30, tzinfo=madrid)
        after_midnight = datetime(2030, 6, 11, 0, 30, tzinfo=madrid)
        self.assertTrue(module.is_upcoming(event, as_of=before_midnight))
        self.assertFalse(module.is_upcoming(event, as_of=after_midnight))

    def test_timed_event_uses_absolute_instant(self):
        event = {'startDate': '2030-06-10T19:00:00+02:00', 'endDate': '2030-06-10T20:00:00+02:00'}
        self.assertTrue(module.is_upcoming(event, as_of=datetime(2030, 6, 10, 17, 59, tzinfo=timezone.utc)))
        self.assertFalse(module.is_upcoming(event, as_of=datetime(2030, 6, 10, 18, 1, tzinfo=timezone.utc)))

if __name__ == '__main__':
    unittest.main()
