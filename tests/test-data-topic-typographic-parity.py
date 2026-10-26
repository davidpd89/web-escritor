import html
import json
import pathlib
import re
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/topic-collections.json'


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'template'):
            self.hidden_depth += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'template') and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data):
        if not self.hidden_depth:
            self.parts.append(data)


def normalize(value):
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


class TopicTypographyParity(unittest.TestCase):
    def test_ready_collection_titles(self):
        data = json.loads(SOURCE.read_text(encoding='utf-8'))
        ready = [item for item in data['collections'] if item['status'] == 'ready']
        self.assertTrue(ready, f'{SOURCE}: ninguna colección ready comprobada')
        for item in ready:
            route = ROOT / 'cuaderno' / 'temas' / item['slug'] / 'index.html'
            self.assertTrue(route.is_file(), f'{SOURCE}: colección {item["slug"]} sin HTML {route}')
            parser = VisibleText()
            parser.feed(route.read_text(encoding='utf-8'))
            visible = normalize(' '.join(parser.parts))
            for title in [item['title']] + [entry['title'] for entry in item['items']]:
                self.assertIn(normalize(title), visible, f'{route}: título editorial ausente o alterado: {title!r}')


if __name__ == '__main__':
    unittest.main()
