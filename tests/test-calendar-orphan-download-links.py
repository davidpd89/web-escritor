import importlib.util
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_orphans', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CalendarOrphanDownloads(unittest.TestCase):
    def test_orphan_calendar_link_is_reported(self):
        html = '<html><body><a data-calendar-download href="/assets/events/calendar/ghost-event.ics">Añadir al calendario</a></body></html>'
        expected, errors = module.expected_calendars(html, as_of=date(2030, 1, 1))
        self.assertEqual(expected, {})
        self.assertTrue(errors, 'El enlace visible apunta a un calendario sin evento JSON-LD')

    def test_unrelated_link_is_not_a_calendar_download(self):
        html = '<a href="/assets/events/calendar/ghost-event.ics">Archivo histórico</a>'
        expected, errors = module.expected_calendars(html, as_of=date(2030, 1, 1))
        self.assertEqual(expected, {})
        self.assertEqual(errors, [])

if __name__ == '__main__':
    unittest.main()
