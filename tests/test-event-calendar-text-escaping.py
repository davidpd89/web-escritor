import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_escape', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CalendarTextEscaping(unittest.TestCase):
    def test_reserved_characters(self):
        cases = {
            'A,B': 'A\\,B',
            'A;B': 'A\\;B',
            'A\\B': 'A\\\\B',
            'A\nB': 'A\\nB',
            'A\r\nB': 'A\\nB',
            'A\rB': 'A\\nB',
            'Niñez, libros; cultura': 'Niñez\\, libros\\; cultura',
        }
        for original, expected in cases.items():
            with self.subTest(original=original):
                self.assertEqual(module._escape_text(original), expected)

    def test_no_raw_newlines_in_text(self):
        for value in ('Primera\nSegunda', 'Primera\rSegunda', 'Primera\r\nSegunda'):
            escaped = module._escape_text(value)
            self.assertNotIn('\n', escaped)
            self.assertNotIn('\r', escaped)
            self.assertIn('\\n', escaped)

if __name__ == '__main__':
    unittest.main()
