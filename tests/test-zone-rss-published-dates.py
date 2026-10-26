import importlib.util
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dated_feed', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class PublishedDates(unittest.TestCase):
    def test_real_articles_keep_publication_instants(self):
        items, _ = feed.collect_items()
        expected = {item['url']: item for item in items if item.get('url') and item.get('title')}
        nodes = ET.parse(ROOT / 'cuaderno/feed.xml').getroot().findall('./channel/item')
        self.assertTrue(nodes, 'cuaderno/feed.xml: canal sin entradas')
        instants = []
        for node in nodes:
            url = node.findtext('link')
            self.assertIn(url, expected, f'cuaderno/feed.xml: URL desconocida {url}')
            source_date = expected[url].get('date')
            published = node.findtext('pubDate')
            if not source_date:
                self.assertFalse(published, f'{url}: fecha RSS sin fecha editorial de origen')
                continue
            self.assertTrue(published, f'{url}: falta pubDate')
            original = datetime.fromisoformat(source_date.replace('Z', '+00:00'))
            if original.tzinfo is None:
                original = original.replace(tzinfo=timezone.utc)
            actual = parsedate_to_datetime(published)
            self.assertEqual(actual.astimezone(timezone.utc), original.astimezone(timezone.utc).replace(microsecond=0), f'{url}: fecha de publicación alterada')
            instants.append(actual.timestamp())
        self.assertEqual(instants, sorted(instants, reverse=True), 'cuaderno/feed.xml: artículos fechados fuera de orden cronológico')

if __name__ == '__main__':
    unittest.main()
