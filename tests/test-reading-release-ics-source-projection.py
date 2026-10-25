#!/usr/bin/env python3
"""Proyección unitaria de los lanzamientos reales al calendario ICS."""
import importlib.util
import json
import unittest
from datetime import date, timedelta
from pathlib import Path
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_release_projection', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
DATA = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))


class ReleaseProjection(unittest.TestCase):
    def test_ics_preserves_exact_source_identity_and_dates(self):
        books = [b for b in DATA['libros'] if b['estado'] == 'publicado']
        expected = {b['id'].lower() + '@davidportodiaz.com': b for b in builder.upcoming_books(books)}
        payload = builder.render_release_ics(books)
        events = [node for node in Calendar.from_ical(payload).walk() if node.name == 'VEVENT']
        actual = {str(event['UID']): event for event in events}
        self.assertEqual(len(actual), len(events), 'Calendario de recomendaciones: UID duplicados')
        self.assertEqual(set(actual), set(expected), 'Calendario de recomendaciones: faltan o sobran títulos publicados')
        for uid, book in expected.items():
            with self.subTest(book=book['slug']):
                event = actual[uid]
                start = date.fromisoformat(book['fecha_publicacion'])
                self.assertEqual(event['DTSTART'].dt, start, f'{book["slug"]}: fecha ICS distinta de {start}')
                self.assertEqual(event['DTEND'].dt, start + timedelta(days=1), f'{book["slug"]}: fin de evento incorrecto')
                self.assertEqual(str(event['SUMMARY']), 'Sale a la venta: ' + book['titulo'], f'{book["slug"]}: título ICS incorrecto')
                self.assertEqual(str(event['URL']), builder.SITE + builder.url(book), f'{book["slug"]}: URL de ficha incorrecta')


if __name__ == '__main__':
    unittest.main()
