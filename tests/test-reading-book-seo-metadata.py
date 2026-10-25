import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://davidportodiaz.com'

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.titles = []
        self.descriptions = []
        self.canonicals = []
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == 'title':
            self.in_title = True
            self.titles.append('')
        if tag == 'meta' and (data.get('name') or '').lower() == 'description':
            self.descriptions.append(data.get('content', ''))
        if tag == 'link' and 'canonical' in (data.get('rel') or '').lower().split():
            self.canonicals.append(data.get('href'))
    def handle_data(self, data):
        if self.in_title:
            self.titles[-1] += data
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

class BookSeo(unittest.TestCase):
    def test_published_pages(self):
        books = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']
        published = [b for b in books if b.get('estado') == 'publicado']
        self.assertTrue(published)
        for book in published:
            with self.subTest(book=book['slug']):
                file = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
                self.assertTrue(file.is_file())
                parser = Metadata()
                parser.feed(file.read_text(encoding='utf-8'))
                self.assertEqual(len(parser.titles), 1)
                self.assertTrue(parser.titles[0].strip())
                self.assertEqual(len(parser.descriptions), 1)
                self.assertTrue(parser.descriptions[0].strip())
                self.assertEqual(parser.canonicals, [SITE + '/recomendaciones/libros/' + book['slug'] + '/'])

if __name__ == '__main__':
    unittest.main()