"""Páginas de género rastreables (/recomendaciones/generos/<slug>/): existen para los géneros con libros suficientes,
llevan CollectionPage + ItemList válidos, están en el sitemap y las etiquetas de las fichas enlazan a ellas en vez de a
un fragmento (#genero=…) que ningún buscador ni asistente de IA indexa."""
import collections
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalogue_builder', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def graph(path):
    html = path.read_text(encoding='utf-8')
    return html, json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)[1])['@graph']


def expected_hubs():
    data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    published = {b['id'] for b in data['libros'] if b['estado'] == 'publicado'}
    genres = {c['id']: c for c in data['categorias'] if c['tipo'] == 'genero' and c['activa']}
    counts = collections.Counter(r['categoria_id'] for r in data['libro_categorias']
                                 if r['libro_id'] in published and r['categoria_id'] in genres)
    return {genres[i]['slug']: n for i, n in counts.items() if n >= builder.GENRE_HUB_MIN}


class GenreHubsTest(unittest.TestCase):
    def test_one_page_per_genre_with_enough_books(self):
        hubs = expected_hubs()
        self.assertGreater(len(hubs), 10)
        pages = {p.parent.name for p in (ROOT / 'recomendaciones/generos').glob('*/index.html')
                 if 'noindex' not in p.read_text(encoding='utf-8')[:400]}
        self.assertEqual(pages, set(hubs))
        # Ejemplos que deben existir siempre con este catálogo: las búsquedas «novedades de romantasy/fantasía/thriller».
        for slug in ('fantasia', 'romantasy', 'misterio-y-thriller', 'novela-historica'):
            self.assertIn(slug, pages)

    def test_page_markup_and_item_list(self):
        for slug in ('romantasy', 'fantasia'):
            path = ROOT / 'recomendaciones/generos' / slug / 'index.html'
            html, nodes = graph(path)
            types = [n['@type'] for n in nodes]
            self.assertEqual(types, ['CollectionPage', 'ItemList', 'BreadcrumbList'])
            page, items = nodes[0], nodes[1]
            canonical = f'https://davidportodiaz.com/recomendaciones/generos/{slug}/'
            self.assertIn(f'<link rel="canonical" href="{canonical}">', html)
            self.assertEqual(page['mainEntity']['@id'], items['@id'])
            self.assertEqual(items['numberOfItems'], len(items['itemListElement']))
            self.assertGreater(items['numberOfItems'], 10)
            for i, item in enumerate(items['itemListElement'], 1):
                self.assertEqual(item['position'], i)
                rel = item['url'].removeprefix('https://davidportodiaz.com/')
                self.assertTrue((ROOT / rel / 'index.html').exists(), item['url'])
            self.assertRegex(page['dateModified'], r'^\d{4}-\d{2}-\d{2}$')
            self.assertIn('Preguntas frecuentes', html)
            self.assertLessEqual(len(re.search(r'<title>(.*?)</title>', html)[1]), 75)

    def test_book_tags_link_to_the_genre_page(self):
        sample = (ROOT / 'recomendaciones/generos/romantasy/index.html').read_text(encoding='utf-8')
        first = re.search(r'"url": "https://davidportodiaz\.com/(recomendaciones/libros/[^"]+)"', sample)[1]
        book = (ROOT / first / 'index.html').read_text(encoding='utf-8')
        self.assertIn('href="/recomendaciones/generos/romantasy/"', book)
        self.assertNotIn('href="/recomendaciones/#genero=romantasy"', book)

    def test_in_sitemap_registry_and_publisher_allowlist(self):
        sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
        registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
        ids = {e['id'] for e in registry['entries']}
        spec_pub = importlib.util.spec_from_file_location('publish_reading', ROOT / 'scripts/publish-reading-refresh.py')
        publisher = importlib.util.module_from_spec(spec_pub)
        spec_pub.loader.exec_module(publisher)
        self.assertTrue(publisher.allowed_path('recomendaciones/generos/index.html'))
        for slug in expected_hubs():
            self.assertIn(f'<loc>https://davidportodiaz.com/recomendaciones/generos/{slug}/</loc>', sitemap)
            self.assertIn('reading-genre-' + slug, ids)
            self.assertTrue(publisher.allowed_path(f'recomendaciones/generos/{slug}/index.html'))

    def test_news_feeds_are_valid_rss_with_real_items(self):
        import xml.etree.ElementTree as ET
        for rel in ('recomendaciones/generos/romantasy/feed.xml', 'recomendaciones/novedades.xml'):
            channel = ET.parse(ROOT / rel).getroot().find('channel')
            items = channel.findall('item')
            self.assertGreater(len(items), 5, rel)
            self.assertLessEqual(len(items), builder.GENRE_FEED_ITEMS)
            for item in items:
                link = item.findtext('link')
                self.assertTrue((ROOT / link.removeprefix('https://davidportodiaz.com/') / 'index.html').exists(), link)
                self.assertTrue(item.findtext('pubDate'))
        page = (ROOT / 'recomendaciones/generos/romantasy/index.html').read_text(encoding='utf-8')
        self.assertIn('type="application/rss+xml"', page)
        self.assertIn('href="/recomendaciones/generos/romantasy/feed.xml"', page)
        self.assertIn('href="/recomendaciones/novedades.xml"', (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8'))

    def test_stale_genre_becomes_noindex_redirect(self):
        page = builder.genre_redirect('fantasia-oscura')
        self.assertIn('noindex', page)
        self.assertIn('/recomendaciones/#genero=fantasia-oscura', page)
        self.assertNotIn('rel="canonical"', page)


if __name__ == '__main__':
    unittest.main()
