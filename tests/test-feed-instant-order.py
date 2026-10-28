import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_order', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

def article(path, title, when):
    node = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': title,
         'url': 'https://davidportodiaz.com/cuaderno/' + title + '/',
         'datePublished': when, 'description': title}
    ]}
    path.write_text('<html><head><script type="application/ld+json">' +
        json.dumps(node) + '</script></head><body></body></html>', encoding='utf-8')

class FeedChronologyTests(unittest.TestCase):
    def test_order_independent_of_offset_notation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            early, late = root / 'early.html', root / 'late.html'
            article(early, 'early', '2026-07-02T00:30:00+02:00')
            article(late, 'late', '2026-07-01T23:45:00Z')
            original = feed.find_html_files
            try:
                feed.find_html_files = lambda: [early, late]
                items, skipped = feed.collect_items()
            finally:
                feed.find_html_files = original
            self.assertEqual(len(items), 2, (items, skipped))
            self.assertEqual([x['title'] for x in items], ['late', 'early'])

if __name__ == '__main__':
    unittest.main()
