#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICS = ROOT / 'convocatorias-escritores/deadlines.ics'

class IcsFolding(unittest.TestCase):
    def test_physical_lines(self):
        raw = ICS.read_bytes()
        self.assertTrue(raw)
        self.assertNotIn(b'\r\r\n', raw)
        self.assertNotIn(b'\n\n', raw)
        self.assertNotIn(b'\xef\xbb\xbf', raw[:3])
        self.assertNotIn(b'\n', raw.replace(b'\r\n', b''), 'Se encontraron saltos LF sin CRLF')
        lines = raw.split(b'\r\n')
        self.assertTrue(lines[0] == b'BEGIN:VCALENDAR')
        self.assertTrue(lines[-2] == b'END:VCALENDAR')
        for index, line in enumerate(lines[:-1], 1):
            self.assertLessEqual(len(line), 75, f'Línea {index}: {len(line)} octetos')
            try:
                line.decode('utf-8')
            except UnicodeDecodeError as exc:
                self.fail(f'Línea {index}: carácter UTF-8 dividido: {exc}')
            if line.startswith((b' ', b'\t')):
                self.assertGreater(index, 1)
                self.assertTrue(lines[index - 2], f'Línea {index}: continuación huérfana')

if __name__ == '__main__':
    unittest.main()
