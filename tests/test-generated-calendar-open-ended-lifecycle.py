import importlib.util
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_lifecycle', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CalendarOpenEndedLifecycle(unittest.TestCase):
    def test_date_only_event_without_end_date(self):
        event = {'startDate': '2030-06-10'}
        self.assertTrue(mod.is_upcoming(event, as_of=date(2030, 6, 9)))
        self.assertTrue(mod.is_upcoming(event, as_of=date(2030, 6, 10)))
        self.assertFalse(mod.is_upcoming(event, as_of=date(2030, 6, 11)))

    def test_timed_event_without_end_date(self):
        event = {'startDate': '2030-06-10T19:00:00+02:00'}
        from datetime import datetime, timezone
        self.assertTrue(mod.is_upcoming(event, as_of=datetime(2030, 6, 10, 16, 59, tzinfo=timezone.utc)))
        self.assertFalse(mod.is_upcoming(event, as_of=datetime(2030, 6, 10, 17, 1, tzinfo=timezone.utc)))

if __name__ == '__main__':
    unittest.main()
