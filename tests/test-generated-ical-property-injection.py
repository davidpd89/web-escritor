import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ical_injection', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class IcalPropertyInjection(unittest.TestCase):
    def test_embedded_property_syntax_remains_text(self):
        event = {
            '@id': 'https://davidportodiaz.com/eventos.html#inyeccion',
            'name': 'Firma\r\nSTATUS:CANCELLED',
            'description': 'Descripción\nBEGIN:VEVENT\nUID:otro@ejemplo.org',
            'startDate': '2030-06-10',
        }
        raw = mod.build_ics(event).decode('utf-8')
        unfolded = raw.replace('\r\n ', '')
        lines = unfolded.split('\r\n')
        self.assertEqual(lines.count('BEGIN:VEVENT'), 1)
        self.assertEqual(lines.count('END:VEVENT'), 1)
        self.assertEqual(lines.count('STATUS:CANCELLED'), 0)
        self.assertEqual(sum(line.startswith('UID:') for line in lines), 1)
        self.assertTrue(any('STATUS:CANCELLED' in line for line in lines if line.startswith('SUMMARY:')))
        self.assertTrue(any('BEGIN:VEVENT' in line for line in lines if line.startswith('DESCRIPTION:')))

if __name__ == '__main__':
    unittest.main()
