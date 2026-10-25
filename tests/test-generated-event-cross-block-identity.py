import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_identity', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class EventCrossBlockIdentity(unittest.TestCase):
    def test_duplicate_event_ids_across_scripts_are_rejected(self):
        event = {
            '@type': 'Event',
            '@id': 'https://davidportodiaz.com/eventos.html#evento-duplicado',
            'name': 'Firma de prueba',
            'startDate': '2030-06-10',
            'endDate': '2030-06-10',
            'eventStatus': mod.EVENT_SCHEDULED,
        }
        script = lambda value: '<script type="application/ld+json">' + json.dumps(value) + '</script>'
        html = script(event) + script(dict(event)) + '<a data-calendar-download href="/assets/events/calendar/evento-duplicado.ics">Calendario</a>'
        expected, errors = mod.expected_calendars(html, as_of=date(2030, 1, 1))
        self.assertTrue(errors, 'Un identificador repetido debe invalidar la generación')
        self.assertTrue(any('duplicad' in error.lower() for error in errors))
        self.assertLessEqual(len(expected), 1)

if __name__ == '__main__':
    unittest.main()
