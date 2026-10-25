import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_folding', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Utf8CalendarFolding(unittest.TestCase):
    def test_multibyte_folding_preserves_content(self):
        samples = [
            'SUMMARY:' + 'á' * 100,
            'DESCRIPTION:' + '漢字' * 60,
            'LOCATION:' + '😀' * 40,
            'SUMMARY:' + 'Aá漢😀' * 50,
        ]
        for original in samples:
            with self.subTest(sample=original[:20]):
                lines = module._fold_line(original)
                self.assertGreater(len(lines), 1)
                self.assertEqual(lines[0][0], original[0])
                self.assertTrue(all(len(line.encode('utf-8')) <= 75 for line in lines))
                self.assertTrue(all(line.startswith(' ') for line in lines[1:]))
                self.assertEqual(lines[0] + ''.join(line[1:] for line in lines[1:]), original)

    def test_crlf_serialization(self):
        payload = module._render_ical(['BEGIN:VCALENDAR', 'SUMMARY:' + 'ñ' * 100, 'END:VCALENDAR'])
        self.assertNotIn(b'\n', payload.replace(b'\r\n', b''))
        self.assertTrue(payload.endswith(b'\r\n'))
        self.assertTrue(all(len(line) <= 75 for line in payload.split(b'\r\n') if line))

if __name__ == '__main__':
    unittest.main()
