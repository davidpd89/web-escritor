import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.times = []
        self.current = None
        self.scripts = []
        self.script = False
        self.buffer = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
            self.current = a['id']
        if tag == 'time' and self.current and a.get('datetime'):
            self.times.append((self.current, a['datetime']))
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.script = True
            self.buffer = ''

    def handle_data(self, data):
        if self.script:
            self.buffer += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.script:
            self.scripts.append(json.loads(self.buffer))
            self.script = False

class TestParity(unittest.TestCase):
    def test_dates(self):
        for name in ('eventos.html', 'ferias.html'):
            with self.subTest(page=name):
                p = Parser()
                p.feed((ROOT / name).read_text(encoding='utf-8'))
                events = [node for document in p.scripts for node in document.get('@graph', []) if node.get('@type') == 'Event']
                self.assertTrue(events)
                for event in events:
                    fragment = event['@id'].split('#')[-1]
                    self.assertIn(fragment, p.ids)
                    dates = [value for section, value in p.times if section == fragment]
                    self.assertTrue(dates, f'{name}#{fragment}: falta fecha HTML')
                    self.assertTrue(any(value[:10] == event['startDate'][:10] for value in dates), f'{name}#{fragment}: fecha visible distinta')

if __name__ == '__main__':
    unittest.main()
