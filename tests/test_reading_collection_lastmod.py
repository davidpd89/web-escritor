"""Las páginas de autor y de editorial declaran dateModified y llegan al sitemap con lastmod."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collection_date(path):
    html = path.read_text(encoding='utf-8')
    graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)[1])['@graph']
    return next(n for n in graph if n['@type'] == 'CollectionPage').get('dateModified')


class CollectionLastmodTest(unittest.TestCase):
    def test_every_catalogue_url_in_the_sitemap_has_lastmod(self):
        sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
        urls = re.findall(r'<url><loc>(https://davidportodiaz\.com/recomendaciones/(?:libros|autores|editoriales)/[^<]*)</loc>(<lastmod>)?', sitemap)
        self.assertGreater(len(urls), 300)
        self.assertEqual([u for u, lastmod in urls if not lastmod], [])

    def test_author_date_is_never_older_than_its_books(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = [b for b in data['libros'] if b['estado'] == 'publicado']
        for path in sorted((ROOT / 'recomendaciones/autores').glob('*/index.html'))[:40]:
            html = path.read_text(encoding='utf-8')
            own = [b['fecha_actualizacion'] for b in books if f"/recomendaciones/libros/{b['slug']}/" in html]
            self.assertTrue(own, path)
            self.assertGreaterEqual(collection_date(path), max(own), path)


if __name__ == '__main__':
    unittest.main()
