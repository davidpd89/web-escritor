import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.frames = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('iframe', 'object', 'embed'):
            self.frames += 1
        for attr in ('src', 'href'):
            if a.get(attr):
                self.refs.append(a[attr])

class TestOfflineIsolation(unittest.TestCase):
    def test_local_dependencies(self):
        html = (ROOT / 'offline.html').read_text(encoding='utf-8')
        p = Resources()
        p.feed(html)
        self.assertEqual(p.frames, 0)
        for ref in p.refs:
            with self.subTest(resource=ref):
                self.assertFalse(urlsplit(ref).scheme in ('http', 'https'))
                self.assertFalse(ref.startswith('//'))
        self.assertNotIn('document.write(', html)
        self.assertNotIn('import(', html)

if __name__ == '__main__':
    unittest.main()