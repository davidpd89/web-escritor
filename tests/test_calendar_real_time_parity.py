import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('real_calendar', ROOT / 'scripts/build-event-calendars.py')
cal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cal)

class CalendarTimeParity(unittest.TestCase):
    def test_real_event_datetimes_are_preserved(self):
        html = (ROOT / 'eventos.html').read_text(encoding='utf-8')
        for event in cal.extract_events(html):
            start = event.get('startDate')
            end = event.get('endDate')
            if not isinstance(start, str) or cal._is_date_only(start):
                continue
            if not isinstance(end, str) or cal._is_date_only(end):
                continue
            if cal._parse_datetime(end, 'endDate') <= cal._parse_datetime(start, 'startDate'):
                continue
            if event.get('eventStatus', cal.EVENT_SCHEDULED) != cal.EVENT_SCHEDULED:
                continue
            content = cal.build_ics(event).decode('utf-8')
            unfolded = content.replace('\r\n ', '')
            expected_start = cal._parse_datetime(start, 'startDate').strftime('%Y%m%dT%H%M%SZ')
            expected_end = cal._parse_datetime(end, 'endDate').strftime('%Y%m%dT%H%M%SZ')
            self.assertIn('DTSTART:' + expected_start + '\r\n', unfolded, f'eventos.html: DTSTART incorrecto en {event.get("@id")}')
            self.assertIn('DTEND:' + expected_end + '\r\n', unfolded, f'eventos.html: DTEND incorrecto en {event.get("@id")}')

if __name__ == '__main__':
    unittest.main()