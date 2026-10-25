import importlib.util
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ical_provenance', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class IcalDtstampProvenance(unittest.TestCase):
    def test_future_modification_is_not_accepted_as_past_provenance(self):
        reference = datetime(2030, 1, 1, tzinfo=timezone.utc)
        event = {
            '@type': 'Event',
            '@id': 'https://davidportodiaz.com/eventos.html#futuro',
            'name': 'Evento futuro',
            'startDate': '2030-06-10T19:00:00+02:00',
            'endDate': '2030-06-10T20:00:00+02:00',
            'dateModified': '2031-01-01T00:00:00Z',
            'eventStatus': mod.EVENT_SCHEDULED,
        }
        html = '<script type="application/ld+json">' + json.dumps(event) + '</script><a data-calendar-download href="/assets/events/calendar/futuro.ics">Calendario</a>'
        expected, errors = mod.expected_calendars(html, as_of=reference)
        self.assertTrue(errors, 'Una modificación posterior a la fecha de referencia debe detectarse')
        self.assertFalse(expected, 'No debe publicarse un ICS con procedencia futura')

if __name__ == '__main__':
    unittest.main()
