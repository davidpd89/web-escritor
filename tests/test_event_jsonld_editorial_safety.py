import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StructuredData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type', '').lower() == 'application/ld+json':
            self.active = True
            self.parts = []
    def handle_data(self, data):
        if self.active:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.blocks.append(''.join(self.parts))
            self.active = False

def events(value):
    if isinstance(value, list):
        for item in value:
            yield from events(item)
    elif isinstance(value, dict):
        types = value.get('@type', [])
        if types == 'Event' or isinstance(types, list) and 'Event' in types:
            yield value
        for item in value.values():
            yield from events(item)

class EventEditorialSafety(unittest.TestCase):
    def test_event_text_fields(self):
        for filename in ('eventos.html', 'ferias.html'):
            parser = StructuredData()
            parser.feed((ROOT / filename).read_text(encoding='utf-8'))
            found = [event for block in parser.blocks for event in events(json.loads(block))]
            self.assertTrue(found, f'{filename}: no hay eventos JSON-LD')
            for index, event in enumerate(found):
                for field in ('name', 'description'):
                    value = event.get(field)
                    if value is None and field == 'description':
                        continue
                    with self.subTest(page=filename, event=index, field=field):
                        self.assertIsInstance(value, str, f'{filename}: Event {index} {field} no es texto')
                        self.assertTrue(value.strip(), f'{filename}: Event {index} {field} vacío')
                        self.assertIsNone(re.search(r'<\s*/?\s*(?:script|iframe|object|embed|svg|form|img)\b|\bon\w+\s*=|javascript\s*:', value, re.I), f'{filename}: Event {index} {field} contiene contenido activo: {value!r}')

if __name__ == '__main__':
    unittest.main()