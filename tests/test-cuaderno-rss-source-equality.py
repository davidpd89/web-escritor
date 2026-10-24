import json
import re
import unittest
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ARTICLE_TYPES = {'Article', 'BlogPosting', 'NewsArticle', 'TechArticle'}

class FeedEquality(unittest.TestCase):
    def test_feed_matches_published_articles(self):
        articles = {}
        for path in sorted((ROOT / 'cuaderno').rglob('index.html')):
            text = path.read_text(encoding='utf-8')
            robots = re.search(r'<meta[^>]*name=[\'"]robots[\'"][^>]*>', text, re.I)
            if robots and 'noindex' in robots.group(0).lower():
                continue
            matches = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', text, re.I | re.S)
            for raw in matches:
                document = json.loads(raw)
                graph = document.get('@graph', [document]) if isinstance(document, dict) else document
                for node in graph:
                    if not isinstance(node, dict):
                        continue
                    kinds = node.get('@type', [])
                    kinds = [kinds] if isinstance(kinds, str) else kinds
                    if ARTICLE_TYPES.intersection(kinds):
                        url = node['url']
                        self.assertNotIn(url, articles, f'Article duplicado {url}')
                        articles[url] = node['datePublished'][:10]
        self.assertTrue(articles, 'No se encontraron artículos publicables')
        root = ET.parse(ROOT / 'cuaderno/feed.xml')
        items = root.findall('./channel/item')
        links = [item.findtext('link') for item in items]
        self.assertEqual(len(links), len(set(links)), 'GUID/URL duplicada')
        self.assertEqual(set(links), set(articles), 'El feed no coincide con la colección publicable')
        for item in items:
            url = item.findtext('link')
            self.assertEqual(item.findtext('guid'), url)
            self.assertEqual(parsedate_to_datetime(item.findtext('pubDate')).date(), date.fromisoformat(articles[url]), url)
            self.assertTrue((item.findtext('description') or '').strip(), url)

if __name__ == '__main__':
    unittest.main()
