"""Las fichas se comparten como libro (og:type book con ISBN y autores); autores y editoriales siguen como web."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def meta(html, prop):
    return re.findall(r'<meta property="' + re.escape(prop) + r'" content="([^"]*)"', html)


class OpenGraphBookTest(unittest.TestCase):
    def test_book_pages_declare_book_metadata_matching_the_schema(self):
        pages = sorted(ROOT.glob('recomendaciones/libros/*/index.html'))
        self.assertGreater(len(pages), 100)
        for page in pages:
            html = page.read_text(encoding='utf-8')
            book = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)[1])['@graph'][0]
            self.assertEqual(meta(html, 'og:type'), ['book'], page)
            self.assertEqual(meta(html, 'book:isbn'), [book['isbn']], page)
            self.assertEqual(meta(html, 'book:author'), [a['url'] for a in book['author'] if a.get('url')], page)
            self.assertEqual(meta(html, 'book:release_date'), [book['datePublished']] if 'datePublished' in book else [], page)

    def test_author_and_publisher_pages_stay_websites(self):
        for page in [*ROOT.glob('recomendaciones/autores/*/index.html')][:20]:
            html = page.read_text(encoding='utf-8')
            self.assertEqual(meta(html, 'og:type'), ['website'], page)
            self.assertEqual(meta(html, 'book:isbn'), [], page)


if __name__ == '__main__':
    unittest.main()
