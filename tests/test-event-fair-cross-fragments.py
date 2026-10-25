import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.current_event = None
        self.stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.stack.append((tag, self.current_event))
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'li' and 'event-entry' in a.get('class', '').split():
            self.current_event = a.get('id')
        if tag == 'a' and self.current_event and a.get('href', '').startswith('/ferias.html#'):
            self.links.append((self.current_event, a['href']))

    def handle_endtag(self, tag):
        if self.stack:
            _, previous = self.stack.pop()
            if tag == 'li':
                self.current_event = previous

class TestCrossFragments(unittest.TestCase):
    def test_event_documentation_targets(self):
        source = Links()
        source.feed((ROOT / 'eventos.html').read_text(encoding='utf-8'))
        target = Links()
        target.feed((ROOT / 'ferias.html').read_text(encoding='utf-8'))
        self.assertTrue(source.links, 'No se encontraron enlaces de documentación')
        for event_id, href in source.links:
            fragment = urlsplit(href).fragment
            with self.subTest(event=event_id, href=href):
                self.assertIn(fragment, target.ids)
                self.assertEqual(fragment, event_id, 'El enlace debe identificar la misma feria')

if __name__ == '__main__':
    unittest.main()
