import unittest
from pathlib import Path
from urllib.parse import urlsplit
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]


class PublishedCalendarIntegrity(unittest.TestCase):
    def test_published_calendar_has_real_distinct_events(self):
        source = ROOT / 'convocatorias-escritores/deadlines.ics'
        calendar = Calendar.from_ical(source.read_bytes())
        events = [component for component in calendar.walk() if component.name == 'VEVENT']
        self.assertGreater(len(events), 0, 'A parsed empty calendar must not pass')
        uids = []
        for event in events:
            with self.subTest(summary=str(event.get('SUMMARY', ''))):
                uid = str(event.get('UID', '')).strip()
                summary = str(event.get('SUMMARY', '')).strip()
                self.assertTrue(uid)
                self.assertTrue(summary)
                self.assertIsNotNone(event.get('DTSTART'))
                self.assertIsNotNone(event.get('DTEND'))
                self.assertGreater(event.decoded('DTEND'), event.decoded('DTSTART'))
                address = str(event.get('URL', '')).strip()
                parsed = urlsplit(address)
                self.assertEqual(parsed.scheme, 'https')
                self.assertTrue(parsed.hostname)
                uids.append(uid)
        self.assertEqual(len(set(uids)), len(uids), 'Duplicate calendar UIDs')


if __name__ == '__main__':
    unittest.main()