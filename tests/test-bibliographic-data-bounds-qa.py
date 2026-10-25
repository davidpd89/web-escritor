import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BibliographicDataBounds(unittest.TestCase):
    def test_book_values(self):
        facts = json.loads((ROOT / 'editorial-facts.json').read_text(encoding='utf-8'))
        for slug, book in facts['books'].items():
            editions = [('principal', book)]
            if 'kindleEdition' in book:
                editions.append(('kindle', book['kindleEdition']))
            for name, edition in editions:
                with self.subTest(book=slug, edition=name):
                    for key in ('numberOfPages', 'printLengthPages', 'priceEUR', 'fileSizeMB'):
                        if key in edition and edition[key] is not None:
                            value = edition[key]
                            self.assertIsInstance(value, (int, float))
                            self.assertNotIsInstance(value, bool)
                            self.assertGreater(value, 0)
                    for key in ('publicationDate', 'verifiedAt'):
                        if edition.get(key):
                            parsed = date.fromisoformat(edition[key])
                            self.assertEqual(parsed.isoformat(), edition[key])
                            if key == 'verifiedAt':
                                self.assertLessEqual(parsed, date.today())
                    if edition.get('publicationYear'):
                        self.assertGreaterEqual(edition['publicationYear'], 1450)
                        self.assertLessEqual(edition['publicationYear'], date.today().year + 2)
                    if edition.get('genres') is not None:
                        self.assertEqual(len(edition['genres']), len(set(edition['genres'])))
                        self.assertTrue(all(isinstance(x, str) and x.strip() for x in edition['genres']))


if __name__ == '__main__':
    unittest.main()