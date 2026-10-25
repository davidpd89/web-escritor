import unittest
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ('editoriales', 'recomendaciones', 'libros', 'lecturas')

class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.robots = ''
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').split():
            self.canonicals.append(a.get('href', ''))
        if tag == 'meta' and a.get('name', '').lower() == 'robots':
            self.robots = a.get('content', '').lower()

class CanonicalTests(unittest.TestCase):
    def test_unique_indexable_canonicals(self):
        seen = defaultdict(list)
        pages = [p for family in FAMILIES for p in (ROOT / family).rglob('*.html')]
        self.assertGreater(len(pages), 0)
        for page in pages:
            parser = Head()
            parser.feed(page.read_text(encoding='utf-8'))
            if 'noindex' in parser.robots:
                continue
            with self.subTest(page=str(page.relative_to(ROOT))):
                self.assertEqual(len(parser.canonicals), 1)
                if len(parser.canonicals) != 1:
                    continue
                url = urlsplit(parser.canonicals[0])
                self.assertEqual(url.scheme, 'https')
                self.assertEqual(url.hostname, 'davidportodiaz.com')
                self.assertFalse(url.query or url.fragment)
                seen[parser.canonicals[0]].append(str(page.relative_to(ROOT)))
        duplicates = {url: paths for url, paths in seen.items() if len(paths) > 1}
        self.assertEqual(duplicates, {})

if __name__ == '__main__':
    unittest.main()