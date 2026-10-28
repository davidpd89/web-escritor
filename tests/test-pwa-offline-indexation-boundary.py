import json
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class RobotsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.directives = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name', '').lower() == 'robots':
            self.directives.extend(re.split(r'[\s,]+', attrs.get('content', '').lower()))


class OfflineIndexationBoundary(unittest.TestCase):
    def test_offline_is_not_indexable_or_a_launch_destination(self):
        parser = RobotsParser()
        parser.feed((ROOT / 'offline.html').read_text(encoding='utf-8'))
        self.assertIn('noindex', parser.directives, 'offline.html: falta noindex')
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        launch_urls = [manifest['start_url']] + [item['url'] for item in manifest.get('shortcuts', [])]
        for url in launch_urls:
            self.assertNotEqual(urlsplit(url).path, '/offline.html', f'manifest.json: destino de lanzamiento offline {url}')
        tree = ET.parse(ROOT / 'sitemap.xml')
        locations = [element.text for element in tree.iter() if element.tag.rsplit('}', 1)[-1] == 'loc']
        self.assertGreater(len(locations), 0, 'sitemap.xml: no se encontraron URLs')
        for location in locations:
            self.assertNotEqual(urlsplit(location).path, '/offline.html', f'sitemap.xml: documento offline indexable {location}')


if __name__ == '__main__':
    unittest.main()