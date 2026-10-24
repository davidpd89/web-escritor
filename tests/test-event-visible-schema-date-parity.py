import importlib.util
import re
import unittest
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('event_dates', ROOT / 'scripts/build-event-calendars.py')
calendar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calendar)

class VisibleDates(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.result = {}
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'li' and 'event-entry' in d.get('class','').split():
            self.current = d.get('id')
        if tag == 'time' and self.current and d.get('datetime'):
            self.result.setdefault(self.current, []).append(d['datetime'])
    def handle_endtag(self, tag):
        if tag == 'li':
            self.current = None

class EventDateParity(unittest.TestCase):
    def test_schema_events_match_visible_dates(self):
        source = (ROOT / 'eventos.html').read_text(encoding='utf-8')
        visible = VisibleDates()
        visible.feed(source)
        events = calendar.extract_events(source)
        self.assertGreater(len(events), 0)
        for event in events:
            fragment = urlsplit(event.get('@id','')).fragment
            if not fragment:
                continue
            with self.subTest(event=fragment):
                self.assertIn(fragment, visible.result)
                start = event['startDate']
                calendar_day = datetime.fromisoformat(start.replace('Z','+00:00')).date()
                parsed = [datetime.fromisoformat(t.replace('Z','+00:00')).date()
                          for t in visible.result[fragment]]
                self.assertIn(calendar_day, parsed)

if __name__ == '__main__':
    unittest.main()
