import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_folding_qa', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class EventUtf8Folding(unittest.TestCase):
    def test_multibyte_folding_is_lossless(self):
        logical = 'SUMMARY:' + ('Árbol ñandú 東京 ' * 20)
        payload = mod._render_ical(['BEGIN:VCALENDAR', logical, 'END:VCALENDAR'])
        self.assertTrue(payload.endswith(b'\r\n'))
        physical = payload.split(b'\r\n')
        self.assertTrue(all(len(line) <= 75 for line in physical))
        text = payload.decode('utf-8')
        unfolded = text.replace('\r\n ', '').split('\r\n')
        self.assertIn(logical, unfolded)

    def test_exact_boundary_does_not_add_continuation(self):
        logical = 'X-TEST:' + 'a' * 68
        self.assertEqual(len(logical.encode('utf-8')), 75)
        self.assertEqual(mod._fold_line(logical), [logical])

if __name__ == '__main__':
    unittest.main()