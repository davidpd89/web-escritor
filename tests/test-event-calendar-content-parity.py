import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'scripts/build-event-calendars.py'
SPEC = importlib.util.spec_from_file_location('event_calendar_parity', PATH)
cal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cal)

class EventCalendarContentParity(unittest.TestCase):
    def test_real_scheduled_events_keep_calendar_content(self):
        html = (ROOT / 'eventos.html').read_text(encoding='utf-8')
        events = cal.extract_events(html)
        checked = 0
        for event in events:
            if event.get('eventStatus') != cal.EVENT_SCHEDULED:
                continue
            checked += 1
            fragment = event['@id'].split('#')[-1]
            with self.subTest(event=fragment):
                ics = cal.build_ics(event).decode('utf-8')
                unfolded = ics.replace('\r\n ', '').replace('\r\n\t', '')
                self.assertIn(
                    'SUMMARY:' + cal._escape_text(event['name'].strip()),
                    unfolded,
                    f'eventos.html#{fragment}: título ICS distinto del JSON-LD',
                )
                for line in cal._event_times(event):
                    self.assertIn(
                        line + '\r\n',
                        unfolded,
                        f'eventos.html#{fragment}: fecha ICS incorrecta: {line}',
                    )
                self.assertEqual(
                    unfolded.count('BEGIN:VEVENT'), 1,
                    f'eventos.html#{fragment}: número de VEVENT incorrecto',
                )
                self.assertEqual(
                    cal.build_ics(event), cal.build_ics(event),
                    f'eventos.html#{fragment}: generación ICS no determinista',
                )
        self.assertGreater(checked, 0, 'eventos.html no contiene eventos programados')

if __name__ == '__main__':
    unittest.main()
