import unittest
from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / 'lecturas/index.html'


class ReadingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots = []
        self.fixtures = []
        self.current = None
        self.depth = 0
        self.text = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name', '').lower() == 'robots':
            self.robots.append(a.get('content', '').lower())
        if tag == 'article' and a.get('data-fixture') == 'true':
            self.current = {'links': [], 'text': ''}
            self.fixtures.append(self.current)
            self.depth = 1
        elif self.current is not None:
            self.depth += 1
            if tag == 'a':
                self.current['links'].append(a.get('href', ''))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.current is not None:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.current is not None:
            self.depth -= 1
            if self.depth == 0:
                self.current = None

    def handle_data(self, data):
        self.text += data
        if self.current is not None:
            self.current['text'] += data


class ReadingFixtureIsolation(unittest.TestCase):
    def test_fixture_not_indexable(self):
        parser = ReadingParser()
        parser.feed(PAGE.read_text(encoding='utf-8'))
        self.assertTrue(parser.fixtures, 'La prueba necesita al menos una tarjeta fixture')
        self.assertEqual(len(parser.robots), 1)
        self.assertIn('noindex', parser.robots[0].replace(' ', '').split(','))
        self.assertIn('fixture', parser.text.lower())
        for fixture in parser.fixtures:
            self.assertIn('ejemplo', fixture['text'].lower())
            self.assertFalse(fixture['links'], 'Las tarjetas de ejemplo no deben llevar a compras')


if __name__ == '__main__':
    unittest.main()