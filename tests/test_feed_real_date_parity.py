import importlib.util
import unittest
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_parity', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedDateParity(unittest.TestCase):
    def test_real_article_dates_survive_rss_serialization(self):
        items, _ = feed.collect_items()
        xml = ET.fromstring(feed.build_feed_bytes(items))
        emitted = {node.findtext('link'): node for node in xml.findall('./channel/item')}
        for source in items:
            if not source.get('title') or not source.get('url'):
                continue
            expected = feed.iso_to_rfc2822(source.get('date')) if source.get('date') else None
            if not expected:
                continue
            self.assertIn(source['url'], emitted, f'RSS: falta artículo {source["path"]}')
            actual = emitted[source['url']].findtext('pubDate')
            self.assertIsNotNone(actual, f'RSS: falta pubDate para {source["path"]}')
            self.assertEqual(parsedate_to_datetime(actual), parsedate_to_datetime(expected), f'RSS: fecha distinta de la fuente {source["path"]}: {actual!r} frente a {expected!r}')

if __name__ == '__main__':
    unittest.main()