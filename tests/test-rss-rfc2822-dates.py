import unittest
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RssDates(unittest.TestCase):
    def test_dates_are_valid_and_sorted(self):
        items = ET.parse(ROOT / 'cuaderno/feed.xml').findall('./channel/item')
        self.assertTrue(items)
        dates = []
        for item in items:
            raw = item.findtext('pubDate')
            with self.subTest(title=item.findtext('title')):
                self.assertTrue(raw)
                value = parsedate_to_datetime(raw)
                self.assertIsNotNone(value.tzinfo)
                dates.append(value.astimezone(timezone.utc))
        self.assertEqual(dates, sorted(dates, reverse=True))

if __name__ == '__main__':
    unittest.main()