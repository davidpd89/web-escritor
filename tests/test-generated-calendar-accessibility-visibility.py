import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_visibility', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CalendarAccessibilityVisibility(unittest.TestCase):
    def test_aria_hidden_ancestor_does_not_satisfy_link_contract(self):
        event = {
            '@type': 'Event',
            '@id': 'https://davidportodiaz.com/eventos.html#accesible',
            'name': 'Firma de libros',
            'startDate': '2030-06-10',
            'endDate': '2030-06-10',
            'eventStatus': mod.EVENT_SCHEDULED,
        }
        script = '<script type="application/ld+json">' + json.dumps(event) + '</script>'
        link = '<a data-calendar-download href="/assets/events/calendar/accesible.ics">Añadir al calendario</a>'
        for wrapper in ('<div aria-hidden="true">', '<section hidden>'):
            with self.subTest(wrapper=wrapper):
                html = script + wrapper + link + ('</div>' if wrapper.startswith('<div') else '</section>')
                _, errors = mod.expected_calendars(html, as_of=date(2030, 1, 1))
                self.assertTrue(errors, 'El enlace oculto no debe satisfacer el contrato')

    def test_visible_link_satisfies_contract(self):
        event = {
            '@type': 'Event',
            '@id': 'https://davidportodiaz.com/eventos.html#accesible',
            'name': 'Firma de libros',
            'startDate': '2030-06-10',
            'eventStatus': mod.EVENT_SCHEDULED,
        }
        html = '<script type="application/ld+json">' + json.dumps(event) + '</script><a data-calendar-download href="/assets/events/calendar/accesible.ics">Añadir al calendario</a>'
        _, errors = mod.expected_calendars(html, as_of=date(2030, 1, 1))
        self.assertFalse(errors)

if __name__ == '__main__':
    unittest.main()
