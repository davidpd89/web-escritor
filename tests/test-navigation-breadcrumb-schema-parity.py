import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['las-manecillas-del-recuerdo/fragmentos/index.html', 'cuaderno/index.html', 'recomendaciones/index.html', 'libros/index.html', 'herramientas/index.html', 'autor.html']


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def item_url(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get('@id') or value.get('url') or ''
    return ''


class BreadcrumbSchemaParity(unittest.TestCase):
    def test_breadcrumb_last_url_matches_canonical(self):
        checked = 0
        for source in PAGES:
            html = (ROOT / source).read_text(encoding='utf-8')
            canonical = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)
            self.assertIsNotNone(canonical, source)
            canonical_url = canonical.group(1).rstrip('/') + '/'
            blocks = re.findall(r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S | re.I)
            for raw in blocks:
                data = json.loads(raw)
                for value in objects(data):
                    if value.get('@type') != 'BreadcrumbList':
                        continue
                    items = value.get('itemListElement', [])
                    self.assertGreaterEqual(len(items), 2, source)
                    self.assertEqual([x.get('position') for x in items], list(range(1, len(items) + 1)), source)
                    urls = [item_url(x.get('item', '')) for x in items]
                    self.assertTrue(all(x.startswith('https://davidportodiaz.com/') for x in urls), source)
                    last = urls[-1]
                    self.assertEqual(urlsplit(last).path.rstrip('/'), urlsplit(canonical_url).path.rstrip('/'), source)
                    self.assertEqual(urlsplit(last).fragment, '', f'{source}: breadcrumb target must be the page, not a fragment')
                    checked += 1
        self.assertGreaterEqual(checked, 3, 'Too few structured breadcrumbs exercised')


if __name__ == '__main__':
    unittest.main()