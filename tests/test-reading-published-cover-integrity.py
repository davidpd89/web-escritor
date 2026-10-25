import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/reading-catalogue.json'

class PublishedCovers(unittest.TestCase):
    def test_local_covers_exist(self):
        books = json.loads(DATA.read_text(encoding='utf-8'))['libros']
        published = [book for book in books if book.get('estado') == 'publicado']
        self.assertTrue(published)
        checked = 0
        for book in published:
            cover = book.get('portada_local')
            if not cover:
                continue
            checked += 1
            with self.subTest(book=book['id']):
                parsed = urlsplit(cover)
                self.assertFalse(parsed.scheme or parsed.netloc or parsed.query or parsed.fragment)
                path = (ROOT / unquote(parsed.path).lstrip('/')).resolve()
                self.assertTrue(path.is_relative_to(ROOT.resolve()))
                self.assertTrue(path.is_file(), str(path))
        self.assertGreater(checked, 0)

if __name__ == '__main__':
    unittest.main()