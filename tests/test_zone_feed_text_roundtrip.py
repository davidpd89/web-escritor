import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_roundtrip', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedTextRoundtripTests(unittest.TestCase):
    def test_real_article_text_survives_xml_serialization(self):
        items, _ = feed.collect_items()
        self.assertTrue(items, 'cuaderno/feed.xml: no hay artículos para verificar')
        xml = ET.fromstring(feed.build_feed_bytes(items))
        published = {node.findtext('link'): node for node in xml.findall('./channel/item')}
        for article in items:
            if not article.get('url') or not article.get('title'):
                continue
            with self.subTest(page=article['path']):
                node = published.get(article['url'])
                self.assertIsNotNone(node, f"{article['path']}: artículo ausente del XML")
                self.assertEqual(node.findtext('title'), article['title'], f"{article['path']}: título modificado al serializar")
                if article.get('description'):
                    self.assertEqual(node.findtext('description'), article['description'], f"{article['path']}: descripción modificada al serializar")

if __name__ == '__main__':
    unittest.main()