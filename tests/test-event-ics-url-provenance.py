import unittest
from pathlib import Path
from urllib.parse import urlsplit
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]

class CalendarUrls(unittest.TestCase):
    def test_event_urls_are_canonical(self):
        files = sorted((ROOT / 'assets/events/calendar').glob('*.ics'))
        self.assertTrue(files)
        checked = 0
        for file in files:
            calendar = Calendar.from_ical(file.read_bytes())
            for event in calendar.walk():
                if event.name != 'VEVENT' or not event.get('URL'):
                    continue
                checked += 1
                url = urlsplit(str(event.get('URL')))
                with self.subTest(file=file.name):
                    self.assertEqual(url.scheme, 'https')
                    self.assertEqual(url.hostname, 'davidportodiaz.com')
                    self.assertIsNone(url.username)
                    self.assertIsNone(url.password)
                    self.assertFalse(url.query)
        self.assertGreater(checked, 0)

if __name__ == '__main__':
    unittest.main()