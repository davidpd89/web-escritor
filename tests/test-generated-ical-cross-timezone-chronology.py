import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ical_chronology', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class IcalCrossTimezoneChronology(unittest.TestCase):
    def test_locally_later_but_absolutely_earlier_end_is_rejected(self):
        event = {
            '@id': 'https://davidportodiaz.com/eventos.html#cronologia',
            'name': 'Evento imposible',
            'startDate': '2030-06-10T19:00:00+02:00',
            'endDate': '2030-06-10T20:00:00+05:00',
        }
        with self.assertRaises(ValueError):
            mod.build_ics(event)

    def test_different_offsets_with_valid_absolute_order(self):
        event = {
            '@id': 'https://davidportodiaz.com/eventos.html#cronologia',
            'name': 'Evento válido',
            'startDate': '2030-06-10T19:00:00+02:00',
            'endDate': '2030-06-10T14:00:00-04:00',
        }
        payload = mod.build_ics(event).decode('utf-8')
        self.assertIn('DTSTART:20300610T170000Z', payload)
        self.assertIn('DTEND:20300610T180000Z', payload)

if __name__ == '__main__':
    unittest.main()
