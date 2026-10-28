import importlib.util
import unittest
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_dates', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedDates(unittest.TestCase):
    def test_real_feed_never_announces_future_publication(self):
        items, _ = feed.collect_items()
        xml = ET.fromstring(feed.build_feed_bytes(items))
        now = datetime.now(timezone.utc)
        for item in xml.findall('./channel/item'):
            title = item.findtext('title')
            value = item.findtext('pubDate')
            if not value:
                continue
            published = parsedate_to_datetime(value)
            self.assertLessEqual(published, now, f'cuaderno/feed.xml: {title!r} anuncia fecha futura {value!r}')

if __name__ == '__main__':
    unittest.main()