import unittest
from pathlib import Path
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / 'assets/events/calendar'

class CalendarUidIntegrity(unittest.TestCase):
    def test_calendar_event_identifiers(self):
        files = sorted(DIR.glob('*.ics'))
        for file in files:
            with self.subTest(file=file.name):
                calendar = Calendar.from_ical(file.read_bytes())
                events = [node for node in calendar.walk() if node.name == 'VEVENT']
                self.assertTrue(events)
                uids = []
                for event in events:
                    uid = str(event.get('UID') or '')
                    self.assertTrue(uid)
                    self.assertIsNotNone(event.get('DTSTART'))
                    try:
                        start = event.decoded('DTSTART')
                    except (ValueError, TypeError, KeyError, OverflowError) as exc:
                        self.fail(f'DTSTART inválido: {exc}')
                    self.assertIsNotNone(start)
                    uids.append(uid)
                self.assertEqual(len(uids), len(set(uids)))

if __name__ == '__main__':
    unittest.main()