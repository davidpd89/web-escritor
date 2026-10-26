import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_publisher_links import render_books

class BookLinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = [dict(attrs).get('href'), '']
    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data
    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(tuple(self.current))
            self.current = None

class EditorialBookBacklinkHomogeneity(unittest.TestCase):
    def test_backlinks_match_published_catalogue(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = data['libros']
        slugs = {b['editorial_slug'] for b in books if b.get('editorial_slug')}
        slugs.update(p.name for p in (ROOT / 'editoriales').iterdir() if p.is_dir() and (p / 'index.html').is_file())
        self.assertTrue(slugs, 'No hay editoriales reales para comprobar')
        for slug in sorted(slugs):
            expected = [b for b in books if b['estado'] == 'publicado' and b.get('editorial_slug') == slug]
            markup = render_books(slug, ROOT)
            if not expected:
                self.assertEqual(markup, '', f'/editoriales/{slug}/: bloque de libros sin títulos publicados')
                continue
            parser = BookLinkParser()
            parser.feed(markup)
            book_links = [(href, label) for href, label in parser.links if href.startswith('/recomendaciones/libros/')]
            expected_links = [(f'/recomendaciones/libros/{b["slug"]}/', b['titulo']) for b in expected]
            self.assertEqual(book_links, expected_links, f'/editoriales/{slug}/: títulos, orden o enlaces distintos del catálogo publicado')
            for href, label in book_links:
                self.assertTrue((ROOT / href.lstrip('/') / 'index.html').is_file(), f'/editoriales/{slug}/: destino inexistente para {label}: {href}')
            self.assertIn('/recomendaciones/', [href for href, _ in parser.links], f'/editoriales/{slug}/: falta enlace al catálogo general')

if __name__ == '__main__':
    unittest.main()