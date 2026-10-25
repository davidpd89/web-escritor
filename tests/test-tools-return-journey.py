import json
import pathlib
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self.links.append(dict(attrs).get('href', ''))

class ReturnJourney(unittest.TestCase):
    def test_return_to_hub(self):
        registry = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
        tools = registry['tools']
        self.assertGreaterEqual(len(tools), 15)
        for tool in tools:
            with self.subTest(tool=tool['slug']):
                path = ROOT / tool['href'].lstrip('/') / 'index.html'
                self.assertTrue(path.is_file())
                parser = LinkParser()
                parser.feed(path.read_text(encoding='utf-8'))
                self.assertIn('/herramientas/', parser.links)

if __name__ == '__main__':
    unittest.main()