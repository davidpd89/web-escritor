import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_expiry', ROOT / 'scripts/build-event-calendars.py')
cal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cal)

class PublishedCalendarExpiry(unittest.TestCase):
    def test_calendar_directory_contains_only_current_events(self):
        source = ROOT / 'eventos.html'
        html = source.read_text(encoding='utf-8')
        now = datetime.now(timezone.utc)
        events = cal.extract_events(html)
        eligible = set()
        for event in events:
            if event.get('eventStatus') != cal.EVENT_SCHEDULED:
                continue
            fragment = cal._event_fragment(event)
            if cal.is_upcoming(event, as_of=now):
                eligible.add(fragment + '.ics')
        directory = ROOT / 'assets/events/calendar'
        actual = {path.name for path in directory.glob('*.ics')} if directory.is_dir() else set()
        self.assertEqual(actual, eligible, f'eventos.html: calendarios caducados o ausentes; sobrantes={sorted(actual - eligible)}, ausentes={sorted(eligible - actual)}')
        for filename in actual:
            content = (directory / filename).read_text(encoding='utf-8')
            self.assertIn('BEGIN:VEVENT', content, f'{filename}: calendario sin evento')
            self.assertIn('STATUS:CONFIRMED', content, f'{filename}: calendario sin estado confirmado')

if __name__ == '__main__':
    unittest.main()
