import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_identity', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CalendarIdentity(unittest.TestCase):
    def test_duplicate_event_identity_across_past_and_future_is_rejected(self):
        common = {'@type': 'Event', '@id': 'https://davidportodiaz.com/eventos.html#feria-repetida', 'eventStatus': module.EVENT_SCHEDULED, 'name': 'Feria repetida'}
        old = dict(common, startDate='2020-01-01')
        future = dict(common, startDate='2030-01-01')
        html = '<script type="application/ld+json">' + json.dumps({'@graph': [old, future]}) + '</script><a data-calendar-download href="/assets/events/calendar/feria-repetida.ics">Calendario</a>'
        try:
            expected, errors = module.expected_calendars(html, as_of=date(2029, 1, 1))
        except ValueError:
            return
        self.assertTrue(errors, 'Identidad duplicada entre evento histórico y futuro')

if __name__ == '__main__':
    unittest.main()
