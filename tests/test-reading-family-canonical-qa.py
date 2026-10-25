import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['libros/index.html', 'recomendaciones/index.html', 'editoriales/index.html']


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.meta = {}
        self.title = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').split():
            self.canonicals.append(a.get('href', ''))
        if tag == 'meta':
            key = a.get('property') or a.get('name')
            if key:
                self.meta.setdefault(key.lower(), []).append(a.get('content', ''))
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


class FamilyCanonicalConsistency(unittest.TestCase):
    def test_family_metadata(self):
        for path in PAGES:
            with self.subTest(path=path):
                parser = MetadataParser()
                parser.feed((ROOT / path).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.canonicals), 1)
                canonical = parser.canonicals[0]
                parsed = urlsplit(canonical)
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(parsed.hostname, 'davidportodiaz.com')
                self.assertFalse(parsed.query or parsed.fragment)
                self.assertEqual(parsed.path, '/' + path.removesuffix('index.html'))
                self.assertEqual(parser.meta.get('og:url'), [canonical])
                self.assertTrue(parser.title.strip())
                self.assertEqual(len(parser.meta.get('description', [])), 1)
                self.assertTrue(parser.meta['description'][0].strip())
                self.assertEqual(len(parser.meta.get('og:title', [])), 1)
                self.assertEqual(len(parser.meta.get('og:description', [])), 1)


if __name__ == '__main__':
    unittest.main()