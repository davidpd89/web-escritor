import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scripts' / 'build-event-calendars.py'

spec = importlib.util.spec_from_file_location('event_calendar_projection', SOURCE)
calendar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calendar)

class CalendarProjection(unittest.TestCase):
    def test_current_published_calendar_projection(self):
        html = (ROOT / 'eventos.html').read_text(encoding='utf-8')
        expected, errors = calendar.expected_calendars(html)
        self.assertFalse(errors,
            'eventos.html: enlaces de calendario incoherentes con EventScheduled: ' + repr(errors))
        self.assertEqual(len(expected), len(set(expected)),
            'eventos.html: nombres de calendarios duplicados')
        for filename, content in expected.items():
            self.assertTrue(filename.endswith('.ics'),
                f'eventos.html: extensión de calendario incorrecta: {filename}')
            self.assertIn(b'BEGIN:VCALENDAR', content,
                f'eventos.html: calendario {filename} sin VCALENDAR')
            self.assertIn(b'BEGIN:VEVENT', content,
                f'eventos.html: calendario {filename} sin VEVENT')
            self.assertIn(b'END:VCALENDAR', content,
                f'eventos.html: calendario {filename} sin cierre VCALENDAR')

if __name__ == '__main__':
    unittest.main()
