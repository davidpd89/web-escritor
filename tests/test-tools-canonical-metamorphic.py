import pathlib
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]

class CanonicalParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'link':
            return
        attributes = dict(attrs)
        if 'canonical' in attributes.get('rel', '').lower().split():
            self.urls.append(attributes.get('href'))

def parse(html):
    parser = CanonicalParser()
    parser.feed(html)
    return parser.urls

class CanonicalMetamorphism(unittest.TestCase):
    def test_equivalent_markup(self):
        pages = sorted((ROOT / 'herramientas').glob('*/index.html'))
        pages.insert(0, ROOT / 'herramientas/index.html')
        self.assertGreaterEqual(len(pages), 15)
        for page in pages:
            with self.subTest(page=str(page)):
                html = page.read_text(encoding='utf-8')
                original = parse(html)
                self.assertEqual(len(original), 1)
                url = original[0]
                self.assertTrue(url.startswith('https://davidportodiaz.com/'))
                variants = [
                    f'<link rel="canonical" href="{url}">',
                    f"<link href='{url}' rel='canonical'>",
                    f'<LINK HREF="{url}" REL="canonical">',
                    f'<link data-test="value" rel="canonical" href="{url}" />'
                ]
                for variant in variants:
                    self.assertEqual(parse(variant), original)

if __name__ == '__main__':
    unittest.main()