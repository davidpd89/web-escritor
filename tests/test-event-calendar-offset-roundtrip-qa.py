import importlib.util
import unittest
from pathlib import Path
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_offset_qa', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class EventOffsetRoundtrip(unittest.TestCase):
    def test_different_offsets_preserve_duration(self):
        event = {
            '@id': 'https://davidportodiaz.com/eventos.html#offset-test',
            'name': 'Evento con cambio de offset',
            'startDate': '2026-10-25T01:30:00+02:00',
            'endDate': '2026-10-25T02:30:00+01:00',
            'eventStatus': 'https://schema.org/EventScheduled'
        }
        calendar = Calendar.from_ical(mod.build_ics(event))
        events = [item for item in calendar.walk() if item.name == 'VEVENT']
        self.assertEqual(len(events), 1)
        start = events[0]['DTSTART'].dt
        end = events[0]['DTEND'].dt
        self.assertEqual((end - start).total_seconds(), 7200)

if __name__ == '__main__':
    unittest.main()