import importlib.util
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'calendar_expiration', ROOT / 'scripts/build-event-calendars.py'
)
cal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cal)

class CalendarExpirationParity(unittest.TestCase):
    def test_real_event_eligibility_matches_event_end(self):
        html = (ROOT / 'eventos.html').read_text(encoding='utf-8')
        events = [
            e for e in cal.extract_events(html)
            if e.get('eventStatus') == cal.EVENT_SCHEDULED
        ]
        self.assertTrue(events, 'eventos.html: no hay eventos programados')
        today = datetime.now(timezone.utc)
        for event in events:
            fragment = event['@id'].split('#')[-1]
            end = event.get('endDate') or event['startDate']
            if cal._is_date_only(end):
                expected = date.fromisoformat(end) >= today.date()
            else:
                expected = cal._parse_datetime(end, 'endDate') >= today
            with self.subTest(event=fragment):
                self.assertEqual(
                    cal.is_upcoming(event, as_of=today), expected,
                    f'eventos.html#{fragment}: elegibilidad ICS incorrecta '
                    f'para endDate={end}',
                )
                if not expected:
                    self.assertNotIn(
                        fragment + '.ics',
                        [p.name for p in (ROOT / 'assets/events/calendar').glob('*.ics')],
                        f'eventos.html#{fragment}: ICS histórico todavía publicado',
                    )

if __name__ == '__main__':
    unittest.main()
