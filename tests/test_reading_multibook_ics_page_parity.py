import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_builder_ics_parity', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class MultiBookIcsParityTests(unittest.TestCase):
    def test_future_dates_match_calendar_and_book_pages(self):
        original = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        template = (ROOT / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
        books = [copy.deepcopy(b) for b in original['libros'] if b['estado'] == 'publicado'][:3]
        self.assertEqual(len(books), 3)
        for book, date in zip(books, ['2032-02-29', '2033-01-01', '2020-01-01']):
            book['fecha_publicacion'] = date
            book['fecha_actualizacion'] = '2026-10-21'
        data = dict(original, libros=books)
        ics = builder.render_release_ics(books)
        unfolded_ics = ics.replace('\r\n ', '').replace('\r\n\t', '')
        self.assertEqual(ics.count('BEGIN:VEVENT'), 2)
        for book in books[:2]:
            self.assertIn('UID:' + book['id'].lower() + '@davidportodiaz.com', ics)
            self.assertIn('URL:' + builder.SITE + builder.url(book), unfolded_ics)
            self.assertIn('DTSTART;VALUE=DATE:' + book['fecha_publicacion'].replace('-', ''), ics)
            page = builder.render_book(data, book, template)
            self.assertIn('Añadir al calendario', page)
            self.assertIn('/' + builder.ICS_PATH, page)
        old = books[2]
        self.assertNotIn('UID:' + old['id'].lower() + '@davidportodiaz.com', ics)
        self.assertNotIn('Añadir al calendario', builder.render_book(data, old, template))

if __name__ == '__main__':
    unittest.main()
