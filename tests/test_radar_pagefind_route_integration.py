import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ROUTE = 'convocatorias-escritores/index.html'


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').split():
            self.canonicals.append(a.get('href', ''))
        if tag == 'meta' and a.get('name', '').lower() == 'robots':
            self.robots.append(a.get('content', '').lower())


class RadarSearchIntegration(unittest.TestCase):
    def test_indexable_route_in_manifest(self):
        path = ROOT / ROUTE
        self.assertTrue(path.is_file(), f'{ROUTE}: falta HTML publicado')
        manifest = json.loads((ROOT / 'pagefind/eligible-manifest.json').read_text(encoding='utf-8'))
        pages = manifest['pages']
        self.assertEqual(pages.count(ROUTE), 1, f'pagefind/eligible-manifest.json: {ROUTE} debe aparecer exactamente una vez')
        metadata = Metadata()
        metadata.feed(path.read_text(encoding='utf-8'))
        self.assertEqual(len(metadata.canonicals), 1, f'{ROUTE}: canonical ausente o duplicada')
        url = urlsplit(metadata.canonicals[0])
        self.assertEqual(url.scheme, 'https', f'{ROUTE}: canonical no HTTPS')
        self.assertEqual(url.path, '/convocatorias-escritores/', f'{ROUTE}: canonical incorrecta')
        self.assertFalse(any('noindex' in value for value in metadata.robots), f'{ROUTE}: noindex incompatible con inclusión en búsqueda')


if __name__ == '__main__':
    unittest.main()
