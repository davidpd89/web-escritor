"""Ficha sintética de todostuslibros: identidad por ISBN, sello y grupo, materias y cubierta propia."""
import io
import json
import sys
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_editorial_sources import SourceError
from reading_ttl_source import sitemap_children, sitemap_products, subjects, ttl_edition, ttl_url, typographic_cover, url_isbn

ISBN = '9788400000011'
PAGE = 'https://www.todostuslibros.com/libros/obra-de-prueba_978-84-00-00001-1'


def document(edition=None, canonical=PAGE, maker='Editorial Prueba Grupo, S.A.U. (Atención al usuario)', **dd):
    work = {'isbn': '978-84-00-00001-1', 'datePublished': '2026-11-20', 'bookFormat': 'https://schema.org/Paperback',
            'numberOfPages': 320, 'inLanguage': 'spa',
            'offers': [{'@type': 'Offer', 'Price': '19.90', 'priceCurrency': 'EUR'}]}
    work.update(edition or {})
    book = {'@context': 'https://schema.org', '@type': 'Book', 'name': 'Obra de prueba',
            'author': [{'@type': 'Person', 'name': 'Apellido, Nombre'}], 'url': canonical, 'workExample': [work]}
    fields = {'Editorial': 'SELLO PRUEBA', 'Fecha publicación': '20-11-2026',
              'Categorías': 'Ficción moderna y contemporánea|Ciencia ficción', 'Colección': 'Serie'}
    fields.update(dd)
    rows = ''.join(f'<dt>{k}:</dt><dd>{v}</dd>' for k, v in fields.items())
    security = f'<div class="block-dato security"><strong>{maker}<br />Calle 1</strong></div>' if maker else ''
    return (f'<link rel="canonical" href="{canonical}">'
            f'<script type="application/ld+json">{json.dumps(book)}</script>'
            f'<dl class="datos-tecnicos">{rows}</dl>'
            '<div id="collapseSynopsis"><p>Una viajera encuentra una carta olvidada y sigue sus pistas hasta una '
            'ciudad abandonada, donde descubre los secretos de una familia separada por la guerra.</p></div>' + security)


class TTLEditionTests(unittest.TestCase):
    def test_reads_edition_group_price_and_subjects(self):
        record = ttl_edition(document(), ttl_url(ISBN))
        self.assertEqual((record['isbn13'], record['titulo'], record['autores']), (ISBN, 'Obra de prueba', ['Nombre Apellido']))
        self.assertEqual((record['editorial'], record['grupo_editorial']), ('SELLO PRUEBA', 'Editorial Prueba Grupo'))
        self.assertEqual((record['fecha_publicacion_edicion'], record['pvp_centimos'], record['numero_paginas']), ('2026-11-20', 1990, 320))
        self.assertEqual(record['materias'], ['narrativa', 'ciencia ficcion'])
        self.assertEqual(record['portada_fuente_url'], PAGE)
        self.assertTrue(record['sinopsis_completa'])

    def test_group_falls_back_to_imprint_without_maker(self):
        self.assertEqual(ttl_edition(document(maker=''), PAGE)['grupo_editorial'], 'SELLO PRUEBA')

    def test_fails_closed(self):
        cases = {'otro ISBN': (document(), ttl_url('9788433951670')),
                 'canónica ajena': (document(canonical='https://example.com/libros/x_9788400000011'), PAGE),
                 'idioma': (document({'inLanguage': 'cat'}), PAGE),
                 'ebook': (document({'bookFormat': 'https://schema.org/EBook'}, Encuadernación='Ebook'), PAGE),
                 'fuera de España': (document({'isbn': '978-0-14-032872-1'},
                                              canonical='https://www.todostuslibros.com/libros/obra_978-0-14-032872-1'),
                                     'https://www.todostuslibros.com/libros/obra_978-0-14-032872-1')}
        for name, (doc, url) in cases.items():
            with self.subTest(name), self.assertRaises(SourceError):
                ttl_edition(doc, url)

    def test_url_helpers(self):
        self.assertEqual(ttl_url('978-84-00-00001-1'), 'https://www.todostuslibros.com/libros/x_' + ISBN)
        self.assertEqual(url_isbn(PAGE), ISBN)
        self.assertIsNone(url_isbn('https://example.com/libros/x_' + ISBN))
        with self.assertRaises(SourceError):
            ttl_url('123')

    def test_sitemap_lists_newest_sheets_and_latest_entries_first(self):
        index = ''.join(f'<sitemap><loc>https://www.todostuslibros.com/sitemap/{n}.xml</loc></sitemap>' for n in (0, 9, 10, 2))
        self.assertEqual(sitemap_children(index, 2), ['https://www.todostuslibros.com/sitemap/10.xml',
                                                      'https://www.todostuslibros.com/sitemap/9.xml'])
        sheet = '<urlset>' + ''.join(f'<url><loc>{u}</loc></url>' for u in (
            PAGE, 'https://www.todostuslibros.com/libros/autoeditado_978-84-09-86237-5',
            'https://www.todostuslibros.com/libros/obra/mapas_978-84-00-00001-1',
            'https://www.todostuslibros.com/libros/reciente_978-84-339-5167-0')) + '</urlset>'
        self.assertEqual(sitemap_products(sheet), ['https://www.todostuslibros.com/libros/reciente_978-84-339-5167-0', PAGE])

    def test_subjects_keep_order_and_limit(self):
        self.assertEqual(subjects('Cómics y novelas gráficas|Infantil|Poesía'), ['comic', 'infantil'])
        self.assertEqual(subjects('Cocina'), ['cocina'])

    def test_typographic_cover_is_own_webp(self):
        cover, preview, size = typographic_cover(ttl_edition(document(), PAGE))
        self.assertEqual(size, (800, 1200))
        self.assertEqual(Image.open(io.BytesIO(cover)).format, 'WEBP')
        self.assertEqual(Image.open(io.BytesIO(preview)).size[0], 320)
        self.assertEqual(cover, typographic_cover(ttl_edition(document(), PAGE))[0])


if __name__ == '__main__':
    unittest.main()
