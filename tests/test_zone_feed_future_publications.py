import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_future', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FuturePublicationTests(unittest.TestCase):
    def test_real_articles_are_not_published_in_future(self):
        items, _ = feed.collect_items()
        self.assertTrue(items, 'cuaderno/feed.xml: no se han descubierto artículos reales')
        now = datetime.now(timezone.utc)
        for item in items:
            with self.subTest(page=item['path']):
                raw = item.get('date')
                self.assertTrue(raw, f"{item['path']}: falta datePublished")
                try:
                    date = datetime.fromisoformat(raw.replace('Z', '+00:00'))
                except ValueError:
                    self.fail(f"{item['path']}: fecha de publicación inválida {raw!r}")
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                self.assertLessEqual(date.astimezone(timezone.utc), now, f"{item['path']}: artículo futuro publicado en RSS: {raw}")

if __name__ == '__main__':
    unittest.main()