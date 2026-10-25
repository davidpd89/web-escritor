import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_origin', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CalendarOriginIntegrity(unittest.TestCase):
    def test_external_event_id_is_rejected(self):
        for origin in ('https://evil.example/eventos.html', 'https://davidportodiaz.com.evil.example/eventos.html', 'http://davidportodiaz.com/eventos.html', 'https://davidportodiaz.com@evil.example/eventos.html'):
            with self.subTest(origin=origin):
                event = {'@id': origin + '#feria-prueba', 'name': 'Feria de prueba', 'startDate': '2030-06-10T19:00:00+02:00'}
                with self.assertRaises(ValueError):
                    module.build_ics(event)

    def test_valid_canonical_event_is_accepted(self):
        event = {'@id': 'https://davidportodiaz.com/eventos.html#feria-prueba', 'name': 'Feria de prueba', 'startDate': '2030-06-10T19:00:00+02:00'}
        result = module.build_ics(event)
        self.assertIn(b'BEGIN:VEVENT', result)

if __name__ == '__main__':
    unittest.main()
