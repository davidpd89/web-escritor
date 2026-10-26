import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_required_fields', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CalendarRequiredFields(unittest.TestCase):
    def test_scheduled_event_without_start_is_not_silently_skipped(self):
        event = {'@type': 'Event', '@id': 'https://davidportodiaz.com/eventos.html#sin-fecha', 'eventStatus': module.EVENT_SCHEDULED, 'name': 'Evento sin fecha'}
        html = '<script type="application/ld+json">' + json.dumps(event) + '</script>'
        try:
            expected, errors = module.expected_calendars(html, as_of=date(2030, 1, 1))
        except ValueError:
            return
        self.assertTrue(errors, 'EventScheduled sin startDate omitido silenciosamente')

if __name__ == '__main__':
    unittest.main()
