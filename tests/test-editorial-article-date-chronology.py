import json
import pathlib
import re
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ArticleChronology(unittest.TestCase):
    def test_dates(self):
        items = ET.parse(ROOT / 'cuaderno/feed.xml').findall('./channel/item')
        self.assertTrue(items)
        for item in items:
            url = item.findtext('link')
            with self.subTest(url=url):
                path = ROOT / urlsplit(url).path.lstrip('/') / 'index.html'
                html = path.read_text(encoding='utf-8')
                blocks = re.findall(r'<script\b[^>]*type=[\x22\x27]application/ld\+json[\x22\x27][^>]*>(.*?)</script>', html, re.S | re.I)
                self.assertTrue(blocks)
                nodes = []
                for block in blocks:
                    obj = json.loads(block)
                    nodes.extend(obj.get('@graph', [obj]))
                articles = [node for node in nodes if node.get('@type') in ('Article', 'BlogPosting', 'NewsArticle')]
                self.assertEqual(len(articles), 1)
                article = articles[0]
                published = datetime.fromisoformat(article['datePublished']).date()
                modified = datetime.fromisoformat(article['dateModified']).date()
                rss = datetime.strptime(item.findtext('pubDate'), '%a, %d %b %Y %H:%M:%S %z').date()
                self.assertEqual(published, rss)
                self.assertGreaterEqual(modified, published)

if __name__ == '__main__':
    unittest.main()