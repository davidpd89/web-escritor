#!/usr/bin/env python3
"""Metamorfismo del orden de nodos JSON-LD."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_graph_order_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

ARTICLE = {
    '@type': 'Article',
    'headline': 'Artículo de prueba',
    'url': 'https://davidportodiaz.com/cuaderno/prueba/',
    'datePublished': '2026-10-20',
    'description': 'Descripción estructurada',
}
OTHERS = [
    {'@type': 'BreadcrumbList', 'itemListElement': []},
    {'@type': 'WebPage', 'name': 'Página contenedora'},
]

class GraphOrder(unittest.TestCase):
    def test_article_position_does_not_change_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'index.html'
            for nodes in ([ARTICLE] + OTHERS, [OTHERS[0], ARTICLE, OTHERS[1]], OTHERS + [ARTICLE]):
                with self.subTest(position=nodes.index(ARTICLE)):
                    payload = json.dumps({'@context': 'https://schema.org', '@graph': nodes}, ensure_ascii=False)
                    path.write_text('<title>Fallback</title><script type="application/ld+json">' + payload + '</script>', encoding='utf-8')
                    actual = feed.extract_metadata(str(path))
                    self.assertEqual(actual['title'], ARTICLE['headline'])
                    self.assertEqual(actual['url'], ARTICLE['url'])
                    self.assertEqual(actual['date'], ARTICLE['datePublished'])
                    self.assertEqual(actual['description'], ARTICLE['description'])
                    self.assertFalse(actual['skip'])

if __name__ == '__main__':
    unittest.main()
