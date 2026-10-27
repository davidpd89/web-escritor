import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CardParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards = []
        self.depth = 0
        self.heading = 0
        self.parts = []
        self.href = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.depth:
            if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
                self.depth += 1
            if tag == 'h3':
                self.heading = self.depth
            if self.heading and tag == 'a':
                self.href = attrs.get('href')
        elif 'data-catalogue-book' in attrs:
            self.depth = 1
            self.heading = 0
            self.parts = []
            self.href = None

    def handle_endtag(self, tag):
        if self.depth:
            if self.depth == self.heading:
                self.heading = 0
            self.depth -= 1
            if not self.depth:
                self.cards.append((self.href, ''.join(self.parts).strip()))

    def handle_data(self, data):
        if self.heading:
            self.parts.append(data)

class CardTitleIntegrityTest(unittest.TestCase):
    def test_long_titles_are_not_shortened(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        html = (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
        parser = CardParser()
        parser.feed(html)
        titles = [title for _, title in parser.cards]
        books = [b for b in data['libros'] if b['estado'] == 'publicado']
        selected = [b for b in books if len(b['titulo']) >= 45 or re.search(r'[¿?():]', b['titulo'])]
        self.assertTrue(selected, 'No se encontraron títulos largos o con puntuación editorial')
        for book in selected:
            with self.subTest(book=book['id']):
                self.assertIn(book['titulo'].strip(), titles, f'recomendaciones/index.html: título incompleto o alterado: {book["titulo"]!r}')

if __name__ == '__main__':
    unittest.main()
