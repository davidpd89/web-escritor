import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class FairParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.times = {}
        self.scripts = []
        self.capture = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'section' and 'fair-record' in a.get('class', '').split():
            self.current = a.get('id')
            self.times[self.current] = []
        if tag == 'time' and self.current and a.get('datetime'):
            self.times[self.current].append(a['datetime'])
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.capture = True
            self.parts = []

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'section' and self.current:
            self.current = None
        if tag == 'script' and self.capture:
            self.scripts.append(''.join(self.parts))
            self.capture = False

class TestFairTimes(unittest.TestCase):
    def test_visible_dates_match_schema(self):
        parser = FairParser()
        parser.feed((ROOT / 'ferias.html').read_text(encoding='utf-8'))
        events = []
        for raw in parser.scripts:
            data = json.loads(raw)
            events.extend(n for n in data.get('@graph', [data]) if n.get('@type') == 'Event')
        self.assertTrue(events)
        for event in events:
            key = urlsplit(event['@id']).fragment
            with self.subTest(event=key):
                self.assertIn(key, parser.times)
                visible = parser.times[key]
                self.assertTrue(visible)
                for field in ('startDate', 'endDate'):
                    value = event[field]
                    self.assertTrue(any(t == value or (len(t) == 10 and value.startswith(t)) for t in visible), f'{key}: {field}={value} no coincide con el HTML')

if __name__ == '__main__':
    unittest.main()
