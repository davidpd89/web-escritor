import json
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.scripts = []
        self.capture = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.capture = True
            self.parts = []

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.scripts.append(''.join(self.parts))
            self.capture = False

class TestEventIdentity(unittest.TestCase):
    def test_schema_resolves_to_visible_record(self):
        for filename in ('eventos.html', 'ferias.html'):
            with self.subTest(page=filename):
                parser = Document()
                parser.feed((ROOT / filename).read_text(encoding='utf-8'))
                counts = Counter(parser.ids)
                events = []
                for raw in parser.scripts:
                    data = json.loads(raw)
                    events.extend(n for n in data.get('@graph', [data]) if n.get('@type') == 'Event')
                self.assertTrue(events, f'{filename}: sin eventos estructurados')
                for event in events:
                    for field in ('@id', 'url'):
                        value = event.get(field, '')
                        parsed = urlsplit(value)
                        self.assertEqual(parsed.netloc, 'davidportodiaz.com')
                        self.assertEqual(parsed.path, '/' + filename)
                        self.assertEqual(counts[parsed.fragment], 1, f'{filename}: {field} no resuelve una entrada única: {value}')

if __name__ == '__main__':
    unittest.main()
