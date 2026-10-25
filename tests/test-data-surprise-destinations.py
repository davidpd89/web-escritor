import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/surprise-content.json').read_text(encoding='utf-8'))

class SurpriseDestinations(unittest.TestCase):
    def test_ready_destinations_are_local_and_unique(self):
        items = [item for item in DATA['items'] if item['status'] == 'ready']
        self.assertTrue(items)
        seen = set()
        for item in items:
            with self.subTest(url=item['url']):
                url = item['url']
                parsed = urlsplit(url)
                self.assertFalse(parsed.scheme or parsed.netloc or parsed.query or parsed.fragment)
                self.assertTrue(url.startswith('/') and url.endswith('/'))
                self.assertNotIn('..', url.split('/'))
                self.assertNotIn('\\', url)
                self.assertNotIn(url, seen)
                seen.add(url)
                target = (ROOT / url.lstrip('/') / 'index.html').resolve()
                self.assertTrue(target.is_relative_to(ROOT.resolve()))
                self.assertTrue(target.is_file(), str(target))

    def test_audiences_and_commercial_flags_are_typed(self):
        for item in DATA['items']:
            with self.subTest(url=item['url']):
                self.assertIs(type(item['commercial']), bool)
                audiences = item['audiences']
                self.assertIsInstance(audiences, list)
                self.assertTrue(audiences)
                self.assertEqual(len(audiences), len(set(audiences)))
                self.assertTrue(set(audiences) <= {'reader', 'writer', 'all'})
                self.assertIsInstance(item['title'], str)
                self.assertTrue(item['title'].strip())
                self.assertEqual(date.fromisoformat(item['reviewed_at']).isoformat(), item['reviewed_at'])

    def test_registry_review_date_is_not_older_than_entries(self):
        registry_date = date.fromisoformat(DATA['reviewed_at'])
        for item in DATA['items']:
            with self.subTest(url=item['url']):
                self.assertLessEqual(date.fromisoformat(item['reviewed_at']), registry_date)

if __name__ == '__main__':
    unittest.main()
