import importlib.util
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_midnight', ROOT / 'scripts/build-event-calendars.py')
cal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cal)

class CalendarMidnightTests(unittest.TestCase):
    def test_date_boundary_matches_madrid_midnight(self):
        cases = [
            ('2026-01-10T00:30:00+01:00', '2026-01-10T00:45:00+01:00', date(2026,1,10)),
            ('2026-07-01T00:30:00+02:00', '2026-07-01T00:45:00+02:00', date(2026,7,1)),
        ]
        madrid = ZoneInfo('Europe/Madrid')
        for start, end, day in cases:
            event = {'startDate':start, 'endDate':end}
            local_midnight = datetime(day.year, day.month, day.day, tzinfo=madrid)
            with self.subTest(start=start):
                expected = cal.is_upcoming(event, as_of=local_midnight)
                self.assertTrue(expected)
                self.assertEqual(cal.is_upcoming(event, as_of=day), expected)

    def test_aware_instants_respect_actual_end(self):
        event = {'startDate':'2026-07-01T00:30:00+02:00',
                 'endDate':'2026-07-01T00:45:00+02:00'}
        self.assertTrue(cal.is_upcoming(event,
            as_of=datetime(2026,6,30,22,40,tzinfo=timezone.utc)))
        self.assertFalse(cal.is_upcoming(event,
            as_of=datetime(2026,6,30,22,46,tzinfo=timezone.utc)))

if __name__ == '__main__':
    unittest.main()
