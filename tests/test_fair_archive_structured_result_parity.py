import json
import unittest
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Archive(HTMLParser):
    def __init__(self):
        super().__init__()
        self.records = {}
        self.stack = []
        self.capture = False
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = a.get('class', '').split()
        if 'fair-record' in classes:
            self.records[a.get('id', '')] = {'dates': []}
            self.stack.append(a.get('id', ''))
        elif self.stack:
            self.stack.append(None)
        if tag == 'time' and self.stack and a.get('datetime'):
            key = next((x for x in self.stack if x), None)
            if key:
                self.records[key]['dates'].append(a['datetime'])
        if tag == 'script' and a.get('type', '').lower() == 'application/ld+json':
            self.capture = True
            self.parts = []

    def handle_data(self, data):
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.blocks.append(''.join(self.parts))
            self.capture = False
        if self.stack and tag not in ('img', 'br', 'hr', 'input', 'meta', 'link', 'source', 'wbr'):
            self.stack.pop()

class FairParity(unittest.TestCase):
    def test_archive_records_are_backed_by_structured_events(self):
        html = (ROOT / 'ferias.html').read_text(encoding='utf-8')
        parser = Archive()
        parser.feed(html)
        events = []
        for block in parser.blocks:
            payload = json.loads(block)
            nodes = payload.get('@graph', [payload])
            events.extend(n for n in nodes if n.get('@type') == 'Event')
        self.assertTrue(events, 'ferias.html: no hay eventos JSON-LD para comparar')
        self.assertTrue(parser.records, 'ferias.html: no hay registros .fair-record')
        for event in events:
            fragment = unquote(urlsplit(event.get('url', event.get('@id', ''))).fragment)
            self.assertIn(fragment, parser.records,
                f'ferias.html: Event {event.get("name")} no tiene registro .fair-record')
            start = event.get('startDate', '')[:10]
            self.assertRegex(start, r'^\d{4}-\d{2}-\d{2}$',
                f'ferias.html: fecha de inicio inválida en {fragment}: {start}')
            date.fromisoformat(start)
        self.assertEqual(len(events), len(parser.records),
            f'ferias.html: {len(events)} eventos JSON-LD frente a {len(parser.records)} registros documentales')

if __name__ == '__main__':
    unittest.main()
