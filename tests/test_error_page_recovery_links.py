import html.parser
import pathlib
import unittest
from urllib.parse import unquote, urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]

class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self.links.append(dict(attrs).get('href', ''))

class TestRecoveryLinks(unittest.TestCase):
    def test_internal_recovery_links(self):
        parser = Links()
        parser.feed((ROOT / '404.html').read_text(encoding='utf-8'))
        self.assertTrue(parser.links)
        for href in parser.links:
            with self.subTest(href=href):
                self.assertTrue(href.strip(), 'Empty destination')
                parsed = urlsplit(href)
                self.assertNotIn(parsed.scheme.lower(), ('javascript', 'data', 'vbscript'))
                if parsed.scheme or parsed.netloc:
                    continue
                path = unquote(parsed.path)
                self.assertFalse(any(part == '..' for part in pathlib.PurePosixPath(path).parts))
                if not path or path == '#':
                    continue
                if path.startswith('/'):
                    candidate = ROOT / path.lstrip('/')
                    if path.endswith('/') or candidate.is_dir():
                        candidate = candidate / 'index.html'
                    self.assertTrue(candidate.is_file(), f'Missing destination: {href}')
                if parsed.fragment and not parsed.path:
                    self.assertIn('id="' + parsed.fragment + '"', (ROOT / '404.html').read_text(encoding='utf-8'))

if __name__ == '__main__':
    unittest.main()
