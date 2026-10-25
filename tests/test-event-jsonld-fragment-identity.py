import importlib.util
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_calendar_identity', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

class EventIdentity(unittest.TestCase):
    def test_unique_event_fragments(self):
        events = mod.extract_events((ROOT / 'eventos.html').read_text(encoding='utf-8'))
        self.assertTrue(events)
        ids = []
        for event in events:
            event_id = event.get('@id')
            with self.subTest(event=event_id):
                self.assertIsInstance(event_id, str)
                parsed = urlsplit(event_id)
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(parsed.netloc, 'davidportodiaz.com')
                self.assertEqual(parsed.path, '/eventos.html')
                self.assertTrue(parsed.fragment)
                self.assertEqual(event.get('url'), event_id)
                ids.append(event_id)
        self.assertEqual(len(ids), len(set(ids)))

if __name__ == '__main__':
    unittest.main()