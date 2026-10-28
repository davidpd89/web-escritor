import re
import unittest
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Times(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag == 'time':
            self.values.append(dict(attrs).get('datetime'))

class TestTime(unittest.TestCase):
    def test_datetime_values(self):
        for name in ('eventos.html', 'ferias.html'):
            parser = Times()
            parser.feed((ROOT / name).read_text(encoding='utf-8'))
            self.assertTrue(parser.values)
            for value in parser.values:
                with self.subTest(page=name, value=value):
                    self.assertTrue(value, 'time sin datetime')
                    if re.fullmatch(r'\d{4}', value):
                        self.assertGreaterEqual(int(value), 1)
                    elif 'T' in value:
                        parsed = datetime.fromisoformat(value)
                        self.assertGreaterEqual(parsed.year, 1)
                    else:
                        date.fromisoformat(value)

if __name__ == '__main__':
    unittest.main()
