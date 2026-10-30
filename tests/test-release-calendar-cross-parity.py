#!/usr/bin/env python3
"""Paridad semántica entre catálogo, fichas HTML y calendario ICS.

Incluye reproducción de un desacuerdo entre las fechas de referencia
cuando hay libros publicados y otros todavía en preparación.
No utiliza red ni el reloj del sistema.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/reading-catalogue.json'
ICS = ROOT / 'recomendaciones/proximos-lanzamientos.ics'
CALENDAR_HREF = '/recomendaciones/proximos-lanzamientos.ics'
DOMAIN = '@davidportodiaz.com'
SITE = 'https://davidportodiaz.com'

spec = importlib.util.spec_from_file_location(
    'reading_calendar_cross_parity',
    ROOT / 'scripts/build-reading-catalogue.py',
)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class AnchorCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = [dict(attrs).get('href', ''), []]

    def handle_data(self, data):
        if self.current is not None:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            href, parts = self.current
            self.anchors.append((href, ' '.join(''.join(parts).split())))
            self.current = None


def calendar_links(html):
    parser = AnchorCollector()
    parser.feed(html)
    return [
        href for href, label in parser.anchors
        if href == CALENDAR_HREF and label == 'Añadir al calendario'
    ]


def calendar_events(payload):
    parsed = Calendar.from_ical(payload)
    records = [item for item in parsed.walk() if item.name == 'VEVENT']
    uids = [str(item.get('UID')) for item in records]
    assert len(uids) == len(set(uids)), 'El calendario contiene UID duplicados'
    return dict(zip(uids, records))


class ReleaseCalendarCrossParity(unittest.TestCase):
    def test_committed_calendar_matches_all_published_book_pages(self):
        data = json.loads(DATA.read_text(encoding='utf-8'))
        published = [b for b in data['libros'] if b['estado'] == 'publicado']
        anchor = max(
            (b.get('fecha_actualizacion') or b.get('fecha_verificacion') or '')
            for b in published
        )
        expected = {
            b['id'].lower() + DOMAIN: b
            for b in published
            if b.get('fecha_publicacion', '') > anchor
        }
        events = calendar_events(ICS.read_bytes())
        self.assertEqual(set(events), set(expected), 'Faltan o sobran lanzamientos publicados')

        for uid, book in expected.items():
            with self.subTest(event=uid):
                event = events[uid]
                start = date.fromisoformat(book['fecha_publicacion'])
                self.assertEqual(event.get('DTSTART').dt, start)
                self.assertEqual(str(event.get('SUMMARY')), 'Sale a la venta: ' + book['titulo'])
                self.assertEqual(
                    str(event.get('DESCRIPTION')),
                    ', '.join(book['autores']) + ' · ' + (book.get('editorial') or ''),
                )
                self.assertEqual(
                    str(event.get('URL')),
                    SITE + '/recomendaciones/libros/' + book['slug'] + '/',
                )

        for book in published:
            with self.subTest(page=book['id']):
                page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
                html = page.read_text(encoding='utf-8')
                expected_count = int(book['id'].lower() + DOMAIN in expected)
                self.assertEqual(
                    len(calendar_links(html)), expected_count,
                    f'{book["id"]}: desacuerdo HTML/ICS sobre añadir al calendario',
                )

    def test_unpublished_update_cannot_desynchronize_calendar_and_link(self):
        source = json.loads(DATA.read_text(encoding='utf-8'))
        data = copy.deepcopy(source)
        published_book = next(
            b for b in data['libros']
            if b['id'] == 'isbn-9788467083378'
        )
        preparation_book = next(
            b for b in data['libros']
            if b['id'] == 'isbn-9791388092268'
        )
        self.assertEqual(published_book['estado'], 'publicado')
        self.assertEqual(preparation_book['estado'], 'publicado')

        # Fechas relativas al ancla de los datos: con un lanzamiento fijo
        # (2026-10-28) el escenario caducaba en cuanto el intake diario añadía
        # fichas posteriores, y el test bloqueaba cada publicación del catálogo.
        anchor = date.fromisoformat(builder.data_anchor(
            [b for b in data['libros'] if b['estado'] == 'publicado']
        ))
        release = anchor + timedelta(days=2)
        published_book['fecha_publicacion'] = release.isoformat()
        if published_book.get('anio_publicacion'):
            published_book['anio_publicacion'] = release.year

        preparation_book['estado'] = 'listo'
        preparation_book['fecha_actualizacion'] = (release + timedelta(days=1)).isoformat()

        # Entrada admitida por el esquema real, no un objeto arbitrario.
        validated = builder.validate(data, ROOT)
        ids = {b['id'] for b in validated}
        self.assertIn(published_book['id'], ids)
        self.assertNotIn(preparation_book['id'], ids)

        events = calendar_events(builder.render_release_ics(validated).encode('utf-8'))
        uid = published_book['id'].lower() + DOMAIN
        self.assertIn(uid, events, 'El libro publicado debe seguir en el calendario')

        template = (
            ROOT / 'scripts/templates/reading-catalogue.html.tmpl'
        ).read_text(encoding='utf-8')
        html = builder.render_book(data, published_book, template)
        self.assertEqual(
            len(calendar_links(html)), 1,
            'DEFECTO: el ICS incluye el lanzamiento, pero la ficha oculta su enlace '
            'cuando otro libro no publicado tiene una actualización posterior',
        )


if __name__ == '__main__':
    unittest.main()
