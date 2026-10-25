import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ical_boundaries', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class IcalAllDayBoundaries(unittest.TestCase):
    def test_exclusive_end_date_across_calendar_boundaries(self):
        cases = [
            ('2030-12-31', '2031-01-01', '20301231', '20310102'),
            ('2028-02-28', '2028-02-29', '20280228', '20280301'),
            ('2030-01-31', '2030-02-01', '20300131', '20300202'),
        ]
        for start, end, expected_start, expected_end in cases:
            with self.subTest(start=start, end=end):
                event = {
                    '@id': 'https://davidportodiaz.com/eventos.html#limite',
                    'name': 'Evento de prueba',
                    'startDate': start,
                    'endDate': end,
                }
                payload = mod.build_ics(event).decode('utf-8')
                self.assertIn('DTSTART;VALUE=DATE:' + expected_start + '\r\n', payload)
                self.assertIn('DTEND;VALUE=DATE:' + expected_end + '\r\n', payload)
                self.assertIn('END:VCALENDAR\r\n', payload)

if __name__ == '__main__':
    unittest.main()
