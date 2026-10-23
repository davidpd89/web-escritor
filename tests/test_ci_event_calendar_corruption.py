from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build-event-calendars.py'

class CalendarCorruptionTest(unittest.TestCase):
    def test_check_detects_corruption_without_writing(self):
        event = {'@context': 'https://schema.org', '@type': 'Event', '@id': 'https://davidportodiaz.com/eventos/#ci-fixture-2099', 'eventStatus': 'https://schema.org/EventScheduled', 'name': 'Feria de prueba', 'startDate': '2099-10-25T02:30:00+02:00', 'endDate': '2099-10-25T03:30:00+01:00', 'dateModified': '2099-01-01T00:00:00Z'}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'eventos.html'
            output = root / 'calendar'
            html = '<script type="application/ld+json">' + json.dumps(event) + '</script><a data-calendar-download href="/assets/events/calendar/ci-fixture-2099.ics">Descargar</a>'
            source.write_text(html, encoding='utf-8')
            command = [sys.executable, str(SCRIPT), '--source', str(source), '--output-dir', str(output)]
            def run(*args):
                return subprocess.run(command + list(args), capture_output=True, text=True, timeout=30)
            first = run()
            self.assertEqual(first.returncode, 0, first.stderr)
            ics = output / 'ci-fixture-2099.ics'
            original = ics.read_bytes()
            self.assertIn(b'BEGIN:VEVENT', original)
            self.assertIn(b'DTSTART:20991025T003000Z', original)
            self.assertEqual(run('--check').returncode, 0)
            ics.write_bytes(b'CORRUPTED')
            failed = run('--check')
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(ics.read_bytes(), b'CORRUPTED')
            self.assertEqual(run().returncode, 0)
            self.assertEqual(ics.read_bytes(), original)

if __name__ == '__main__':
    unittest.main()