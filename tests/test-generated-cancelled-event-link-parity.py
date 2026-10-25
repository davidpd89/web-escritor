import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cancelled_event_links', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CancelledEventLinkParity(unittest.TestCase):
    def test_cancelled_event_cannot_keep_download_action(self):
        event = {
            '@type': 'Event',
            '@id': 'https://davidportodiaz.com/eventos.html#cancelado',
            'name': 'Firma cancelada',
            'startDate': '2030-06-10',
            'eventStatus': 'https://schema.org/EventCancelled',
        }
        script = '<script type="application/ld+json">' + json.dumps(event) + '</script>'
        link = '<a data-calendar-download href="/assets/events/calendar/cancelado.ics">Añadir al calendario</a>'
        expected, errors = mod.expected_calendars(script + link, as_of=date(2030, 1, 1))
        self.assertEqual(expected, {})
        self.assertTrue(errors, 'El enlace de un evento cancelado debe rechazarse')

if __name__ == '__main__':
    unittest.main()
