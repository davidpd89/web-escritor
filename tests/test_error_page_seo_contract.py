import html.parser
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class HeadParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.metas = []
        self.links = []
        self.title = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == 'meta':
            self.metas.append(data)
        if tag == 'link':
            self.links.append(data)
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data

class TestErrorSEO(unittest.TestCase):
    def test_error_page_metadata(self):
        for filename in ('404.html', 'offline.html'):
            with self.subTest(filename=filename):
                parser = HeadParser()
                parser.feed((ROOT / filename).read_text(encoding='utf-8'))
                self.assertTrue(parser.title.strip())
                robots = [m.get('content', '') for m in parser.metas if m.get('name', '').lower() == 'robots']
                self.assertEqual(len(robots), 1)
                self.assertIn('noindex', robots[0].lower())
                descriptions = [m.get('content', '') for m in parser.metas if m.get('name', '').lower() == 'description']
                self.assertEqual(len(descriptions), 1)
                self.assertGreater(len(descriptions[0].strip()), 30)
                canonicals = [l for l in parser.links if l.get('rel', '').lower() == 'canonical']
                self.assertEqual(canonicals, [], 'Error pages must not declare a misleading canonical')

if __name__ == '__main__':
    unittest.main()
