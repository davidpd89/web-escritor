import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == 'a' and data.get('href'):
            self.links.append(data['href'])
        if data.get('id'):
            self.anchors.add(data['id'])
        if tag == 'a' and data.get('name'):
            self.anchors.add(data['name'])

class RecommendationLinks(unittest.TestCase):
    def test_internal_destinations(self):
        sources = sorted((ROOT / 'recomendaciones').rglob('*.html'))
        self.assertGreater(len(sources), 0)
        parsed = {}
        def read(file):
            if file not in parsed:
                p = Links()
                p.feed(file.read_text(encoding='utf-8'))
                parsed[file] = p
            return parsed[file]
        checked = 0
        for source in sources:
            for href in read(source).links:
                url = urlsplit(href)
                if url.scheme or url.netloc or href.startswith('//'):
                    continue
                if not url.path and not url.fragment:
                    continue
                raw = unquote(url.path)
                if raw.startswith('/'):
                    destination = ROOT / raw.lstrip('/')
                else:
                    destination = source.parent / raw
                destination = destination.resolve()
                self.assertTrue(destination.is_relative_to(ROOT.resolve()), f'Ruta fuera del sitio: {source}: {href}')
                if destination.is_dir() or raw.endswith('/'):
                    destination /= 'index.html'
                self.assertTrue(destination.is_file(), f'Destino inexistente: {source}: {href}')
                if url.fragment and destination.suffix.lower() in ('.html', '.htm'):
                    self.assertIn(unquote(url.fragment), read(destination).anchors, f'Fragmento inexistente: {source}: {href}')
                checked += 1
        self.assertGreater(checked, 0)

if __name__ == '__main__':
    unittest.main()