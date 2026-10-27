import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://davidportodiaz.com/'

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.graph = []
        self.active = False
        self.buffer = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.active = True
            self.buffer = ''

    def handle_data(self, data):
        if self.active:
            self.buffer += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            data = json.loads(self.buffer)
            self.graph.extend(data.get('@graph', [data]))
            self.active = False

class TestIdentity(unittest.TestCase):
    def test_event_identity(self):
        for page in ('eventos.html', 'ferias.html'):
            with self.subTest(page=page):
                document = Document()
                document.feed((ROOT / page).read_text(encoding='utf-8'))
                self.assertEqual(len(document.ids), len(set(document.ids)), 'ID HTML duplicado')
                events = [x for x in document.graph if x.get('@type') == 'Event']
                self.assertTrue(events)
                identities = [x['@id'] for x in events]
                self.assertEqual(len(identities), len(set(identities)))
                for event in events:
                    with self.subTest(event=event['@id']):
                        for field in ('@id', 'url'):
                            value = urlsplit(event[field])
                            self.assertEqual(value.scheme + '://' + value.netloc + value.path, BASE + page)
                            self.assertTrue(value.fragment)
                            self.assertIn(value.fragment, document.ids)
                        self.assertEqual(event['@id'], event['url'])

if __name__ == '__main__':
    unittest.main()
