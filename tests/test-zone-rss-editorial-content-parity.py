import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('editorial_feed', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class EditorialFeedParity(unittest.TestCase):
    def test_published_feed_preserves_article_copy(self):
        items, _ = feed.collect_items()
        actual = ET.parse(ROOT / 'cuaderno/feed.xml').getroot().findall('./channel/item')
        expected = {item['url']: item for item in items if item.get('url') and item.get('title')}
        self.assertTrue(expected, 'cuaderno/: no se encontraron artículos publicados')
        self.assertEqual(set(expected), {node.findtext('link') for node in actual}, 'cuaderno/feed.xml: entradas distintas de los artículos publicados')
        for node in actual:
            url = node.findtext('link')
            article = expected[url]
            self.assertEqual(node.findtext('title'), article['title'], f'{url}: título RSS distinto del artículo')
            self.assertEqual(node.findtext('description') or '', article.get('description') or '', f'{url}: descripción RSS distinta del artículo')

if __name__ == '__main__':
    unittest.main()
