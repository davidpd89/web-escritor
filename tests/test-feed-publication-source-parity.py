import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'

class JsonBlocks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.parts = []
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.inside = True
            self.parts = []
    def handle_data(self, value):
        if self.inside:
            self.parts.append(value)
    def handle_endtag(self, tag):
        if tag == 'script' and self.inside:
            self.blocks.append(''.join(self.parts))
            self.inside = False

def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)

def instant(text):
    dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

class PublicFeedParity(unittest.TestCase):
    def test_items_match_published_metadata(self):
        root = ET.parse(ROOT / 'cuaderno/feed.xml').getroot()
        items = root.findall('./channel/item')
        self.assertGreater(len(items), 0)
        checked = 0
        for item in items:
            link = item.findtext('link')
            date_text = item.findtext('pubDate')
            self.assertTrue(link and date_text)
            parsed = urlparse(link)
            self.assertEqual(parsed.netloc, 'davidportodiaz.com')
            relative = parsed.path.strip('/')
            path = ROOT / relative / 'index.html'
            if not path.is_file():
                path = ROOT / (relative + '.html')
            self.assertTrue(path.is_file(), str(path))
            parser = JsonBlocks()
            parser.feed(path.read_text(encoding='utf-8'))
            articles = []
            for block in parser.blocks:
                for node in nodes(json.loads(block)):
                    types = node.get('@type', [])
                    types = [types] if isinstance(types, str) else types
                    if any(t in ('Article', 'BlogPosting', 'NewsArticle') for t in types):
                        articles.append(node)
            self.assertTrue(articles, str(path))
            published = articles[0].get('datePublished')
            self.assertTrue(published, str(path))
            actual = parsedate_to_datetime(date_text).astimezone(timezone.utc)
            self.assertEqual(actual, instant(published), link)
            modified = articles[0].get('dateModified')
            if modified and 'T' in published and 'T' in modified:
                self.assertLessEqual(instant(published), instant(modified))
            checked += 1
        self.assertGreater(checked, 0)

if __name__ == '__main__':
    unittest.main()
