import pathlib
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ['fragmento/index.html', 'las-manecillas-del-recuerdo/fragmentos/index.html']

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.canonical = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = attrs.get('property') or attrs.get('name')
            if key:
                self.meta.setdefault(key, []).append(attrs.get('content', ''))
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs.get('href'))

class FragmentSocialParity(unittest.TestCase):
    def test_social_metadata(self):
        for name in PAGES:
            with self.subTest(page=name):
                parser = Metadata()
                parser.feed((ROOT / name).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.canonical), 1)
                for key in ('og:url', 'og:title', 'og:description', 'og:image', 'og:image:alt', 'twitter:title', 'twitter:description', 'twitter:image', 'twitter:image:alt'):
                    self.assertEqual(len(parser.meta.get(key, [])), 1, key)
                    self.assertTrue(parser.meta[key][0].strip(), key)
                self.assertEqual(parser.meta['og:url'][0], parser.canonical[0])
                self.assertEqual(parser.meta['og:image'][0], parser.meta['twitter:image'][0])
                self.assertTrue(parser.meta['og:image'][0].startswith('https://'))
                self.assertEqual(parser.meta.get('twitter:card'), ['summary_large_image'])

if __name__ == '__main__':
    unittest.main()