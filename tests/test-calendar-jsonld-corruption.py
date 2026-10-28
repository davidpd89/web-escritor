import importlib.util
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_corruption', ROOT / 'scripts/build-event-calendars.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CalendarJsonLdCorruption(unittest.TestCase):
    def test_corrupted_event_block_cannot_pass_as_empty_calendar(self):
        html = '<html><head><script type="application/ld+json">{"@type":"Event","name":"Feria", BROKEN}</script></head><body></body></html>'
        try:
            events, errors = module.expected_calendars(html, as_of=date(2030, 1, 1))
        except (ValueError, TypeError):
            return
        self.assertTrue(errors, 'JSON-LD corrupto ignorado: el generador aparenta éxito')

    def test_valid_empty_document_is_distinguishable(self):
        events, errors = module.expected_calendars('<html><body></body></html>', as_of=date(2030, 1, 1))
        self.assertEqual(events, {})
        self.assertEqual(errors, [])

if __name__ == '__main__':
    unittest.main()
