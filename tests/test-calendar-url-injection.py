import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_url_security', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CalendarUrlSecurity(unittest.TestCase):
    def setUp(self):
        self.event = {'@id': 'https://davidportodiaz.com/eventos.html#feria-prueba', 'name': 'Feria', 'startDate': '2030-06-10T19:00:00+02:00'}

    def test_url_property_rejects_injection_and_unsafe_schemes(self):
        values = ['javascript:alert(1)', 'http://example.org/event', 'https://example.org/event\r\nATTENDEE:mailto:attacker@example.org', 'https://user:password@example.org/event']
        for value in values:
            with self.subTest(value=value):
                event = dict(self.event, url=value)
                with self.assertRaises(ValueError):
                    module.build_ics(event)

    def test_canonical_https_url_is_preserved(self):
        payload = module.build_ics(dict(self.event, url='https://davidportodiaz.com/eventos.html#feria-prueba'))
        self.assertIn(b'URL:https://davidportodiaz.com/eventos.html#feria-prueba', payload)

if __name__ == '__main__':
    unittest.main()
