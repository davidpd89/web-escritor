import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

PAGE = Path(__file__).resolve().parents[1] / 'convocatorias-escritores/index.html'


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])


class FragmentTargets(unittest.TestCase):
    def test_local_fragments_resolve(self):
        doc = Document()
        doc.feed(PAGE.read_text(encoding='utf-8'))
        checked = 0
        for href in doc.links:
            u = urlsplit(href)
            if not u.fragment:
                continue
            if u.scheme or u.netloc:
                continue
            if u.path not in ('', '.', '/convocatorias-escritores/', '/convocatorias-escritores/index.html'):
                continue
            target = unquote(u.fragment)
            self.assertIn(target, doc.ids, f'/convocatorias-escritores/: ancla inexistente {href}')
            checked += 1
        self.assertGreater(checked, 0, '/convocatorias-escritores/: no se comprobaron anclas locales')


if __name__ == '__main__':
    unittest.main()
