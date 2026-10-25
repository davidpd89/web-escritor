import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'
FAMILIES = ('lecturas', 'libros', 'recomendaciones', 'editoriales')

class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and a.get('src'):
            self.urls.append(a['src'])
        if tag == 'link' and 'stylesheet' in a.get('rel', '').split() and a.get('href'):
            self.urls.append(a['href'])

class StaticAssetsTests(unittest.TestCase):
    def test_local_assets_exist(self):
        pages = [p for family in FAMILIES for p in (ROOT / family).rglob('*.html')]
        self.assertTrue(pages)
        count = 0
        for page in pages:
            parser = Assets()
            parser.feed(page.read_text(encoding='utf-8'))
            source = ORIGIN + '/' + page.relative_to(ROOT).as_posix().removesuffix('index.html')
            for href in parser.urls:
                url = urlsplit(urljoin(source, href))
                if url.hostname != 'davidportodiaz.com':
                    continue
                target = (ROOT / unquote(url.path).lstrip('/')).resolve()
                count += 1
                with self.subTest(page=str(page.relative_to(ROOT)), resource=href):
                    self.assertTrue(target.is_relative_to(ROOT.resolve()))
                    self.assertTrue(target.is_file(), str(target))
                    self.assertGreater(target.stat().st_size, 0)
        self.assertGreater(count, 0)

if __name__ == '__main__':
    unittest.main()