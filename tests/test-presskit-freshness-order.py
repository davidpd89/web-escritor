import copy
import importlib.util
import io
import json
import unittest
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('press_builder', ROOT / 'scripts/build-press-kit.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
load = lambda p: json.loads((ROOT / p).read_text())

class FreshnessOrder(unittest.TestCase):
    def test_date_follows_latest_source(self):
        book = load('press-kit/las-manecillas-del-recuerdo.json')
        author = load('press-kit/david-porto-diaz.json')
        scenarios = [('2026-10-05', '2026-10-15'), ('2026-11-20', '2026-10-15'), ('2027-01-01', '2027-04-01')]
        for book_date, author_date in scenarios:
            with self.subTest(book=book_date, author=author_date):
                b, a = copy.deepcopy(book), copy.deepcopy(author)
                b['lastUpdated'], a['lastUpdated'] = book_date, author_date
                payload, _ = builder.build_bytes({'assets': [], 'documents': []}, b, a)
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    entry = archive.getinfo('README.txt')
                    stamp = date(*entry.date_time[:3])
                    expected = max(date.fromisoformat(book_date), date.fromisoformat(author_date))
                    self.assertGreaterEqual(stamp, expected)

if __name__ == '__main__':
    unittest.main()