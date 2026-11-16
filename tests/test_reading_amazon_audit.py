import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_amazon_market import audit_book, apply_audit, page_rating, page_synopsis  # noqa: E402
from test_reading_amazon_market import BOOK, SWATCH_PAGE, COVER_PAGE  # noqa: E402

spec = importlib.util.spec_from_file_location('reading_amazon_audit', ROOT / 'scripts/reading-amazon-audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
PAGE = '<span id="productTitle"> Coraline (Edición en español) </span>' + SWATCH_PAGE + COVER_PAGE
# Bloque de valoraciones de una ficha de amazon.es (atributos y orden como los sirve la página).
STARS = ('<div id="averageCustomerReviews" data-asin="8498382378"><span class="a-declarative">'
         '<span id="acrPopover" class="reviewCountTextLinkedHistogram noUnderline" title="4,6 de 5 estrellas">'
         '<a href="#customerReviews"><span class="a-size-base a-color-base"> 4,6 </span>'
         '<i class="a-icon a-icon-star a-star-4-5"><span class="a-icon-alt">4,6 de 5 estrellas</span></i></a></span>'
         '<a id="acrCustomerReviewLink" href="#customerReviews">'
         '<span id="acrCustomerReviewText" aria-label="12.345 valoraciones" class="a-size-base">(12.345)</span></a></div>')


# Bloque de descripción tal como lo sirve amazon.es (16/11, ficha 8408331140), recortado.
DESCRIPTION = ('<div id="bookDescription_feature_div" class="celwidget" data-feature-name="bookDescription">'
               '<div data-a-expander-name="book_description_expander" class="a-expander-collapsed-height a-row">'
               '<div data-expanded="false" class="a-expander-content a-expander-partial-collapse-content">'
               '<p><span>Dicen que las princesas son elegantes, encantadoras y un poquito m&aacute;gicas. '
               'Mora Florentina de Florent&iacute;a no es ninguna de esas cosas.</span></p>'
               '<p><span>Es hija del hada m&aacute;s poderosa del reino, pero no tiene ni un solo poder.</span></p></div>'
               '<div class="a-expander-header a-expander-partial-collapse-header"><a data-action="a-expander-toggle">'
               'Leer m&aacute;s</a></div></div></div>')


class AmazonAuditTests(unittest.TestCase):
    def test_synopsis_is_read_from_the_book_description_block(self):
        text = page_synopsis(PAGE + DESCRIPTION)
        self.assertTrue(text.startswith('Dicen que las princesas son elegantes, encantadoras y un poquito mágicas.'))
        self.assertIn('\n\nEs hija del hada más poderosa', text)
        self.assertNotIn('Leer más', text)
        self.assertEqual(page_synopsis(PAGE), '')
        self.assertEqual(audit_book({**BOOK}, lambda url: PAGE, '2026-11-03')['sinopsis_amazon'], '')

    def test_amazon_synopsis_reaches_only_books_without_one_and_stays_out_of_the_register(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / 'data').mkdir()
            own = {**BOOK, 'id': 'lib-2', 'sinopsis_breve': 'Propia.', 'sinopsis_completa': 'Propia ' * 20,
                   'sinopsis_tipo': 'extracto_editorial', 'sinopsis_fuente_url': 'https://editorial.example/x'}
            (tree / 'data/reading-catalogue.json').write_text(json.dumps({'libros': [{**BOOK}, own]}), encoding='utf-8')
            record = audit_book({**BOOK}, lambda url: PAGE + DESCRIPTION, '2026-11-03')
            stats = audit.apply_records(tree, {'lib-1': record, 'lib-2': record}, 'davidporto-21', covers=0)
            self.assertEqual(stats['synopses_added'], 1)
            books = json.loads((tree / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']
            self.assertEqual(books[0]['sinopsis_fuente_url'], 'https://www.amazon.es/dp/8498382378')
            self.assertEqual(books[0]['sinopsis_tipo'], 'extracto_editorial')
            self.assertTrue(books[0]['sinopsis_completa'].startswith('Dicen que las princesas'))
            self.assertEqual(books[1]['sinopsis_breve'], 'Propia.')
            public = json.loads((tree / 'data/reading-amazon-audit.json').read_text(encoding='utf-8'))['libros']
            self.assertNotIn('sinopsis_amazon', public['lib-1'])

    def test_books_without_synopsis_not_yet_read_for_it_go_first_closest_first(self):
        now = datetime(2026, 11, 3, 12, tzinfo=ZoneInfo('Europe/Madrid'))
        books = [{'id': 'viejo', 'estado': 'publicado', 'fecha_publicacion': '2020-01-01'},
                 {'id': 'cerca', 'estado': 'publicado', 'fecha_publicacion': '2026-11-04'},
                 {'id': 'leido', 'estado': 'publicado', 'fecha_publicacion': '2026-11-03'},
                 {'id': 'con', 'estado': 'publicado', 'sinopsis_breve': 'x'}]
        records = {b: {'fecha': '2026-11-02', 'estado': 'ok'} for b in ('viejo', 'cerca', 'con')}
        records['leido'] = {'fecha': '2026-11-02', 'estado': 'ok', 'sinopsis_amazon': ''}
        self.assertEqual([b['id'] for b in audit.due({'libros': books}, records, now)], ['cerca', 'viejo'])

    def test_book_without_formats_is_found_by_its_isbn10_and_completed(self):
        book = {**BOOK}
        urls = []
        record = audit_book(book, lambda url: urls.append(url) or PAGE, '2026-11-03')
        self.assertEqual(urls, ['https://www.amazon.es/dp/8498382378'])
        self.assertEqual(record['estado'], 'ok')
        self.assertEqual(record['faltan'], ['tapa-blanda', 'ebook', 'audiolibro'])
        self.assertEqual(record['portada_amazon'], 'https://m.media-amazon.com/images/I/51qFSR41gJL.jpg')
        self.assertEqual(apply_audit(book, record, 'davidporto-21'), 3)
        self.assertEqual(book['formatos_compra'][1]['url'], 'https://www.amazon.es/dp/B00EBOOK01?tag=davidporto-21')

    def test_isbn10_page_of_another_work_adds_nothing(self):
        record = audit_book({**BOOK}, lambda url: PAGE.replace('Coraline', 'El libro del cementerio'), '2026-11-03')
        self.assertEqual(record['estado'], 'otra_obra')
        self.assertEqual(apply_audit({**BOOK}, record, 'davidporto-21'), 0)

    def test_shown_format_missing_on_amazon_is_reported_not_removed(self):
        book = {**BOOK, 'formatos_compra': [{'formato': 'tapa-blanda', 'url': 'https://www.amazon.es/dp/8498382378'},
                                            {'formato': 'tapa-dura', 'url': 'https://www.amazon.es/dp/847888579X'}]}
        record = audit_book(book, lambda url: PAGE, '2026-11-03')
        self.assertEqual(record['sin_confirmar'], ['tapa-dura'])
        apply_audit(book, record, 'davidporto-21')
        self.assertIn('tapa-dura', [o['formato'] for o in book['formatos_compra']])

    def test_captcha_is_not_a_record_and_missing_page_is(self):
        self.assertIsNone(audit_book({**BOOK}, lambda url: '<form action="/errors/validateCaptcha">', '2026-11-03'))
        self.assertIsNone(audit_book({**BOOK}, lambda url: 'window.location.href.replace(/[&?]bm-verify=', '2026-11-03'))

        def missing(url):
            raise HTTPError(url, 404, 'Not Found', {}, None)
        self.assertEqual(audit_book({**BOOK}, missing, '2026-11-03')['estado'], 'sin_ficha')
        self.assertEqual(audit_book({**BOOK, 'isbn13': '9791388306181'}, missing, '2026-11-03')['estado'], 'sin_asin')

    def test_every_published_book_is_due_oldest_first_without_a_cap(self):
        books = [{'id': f'b{i}', 'estado': 'publicado', 'sinopsis_breve': 'x'} for i in range(500)] + [{'id': 'x', 'estado': 'borrador'}]
        records = {'b0': {'fecha': '2026-11-02', 'estado': 'ok'}, 'b1': {'fecha': '2026-10-01', 'estado': 'ok'},
                   'b2': {'fecha': '2026-11-02', 'estado': 'sin_ficha'}}
        now = datetime(2026, 11, 3, 12, tzinfo=ZoneInfo('Europe/Madrid'))
        ids = [b['id'] for b in audit.due({'libros': books}, records, now)]
        self.assertEqual(len(ids), 499)  # b0 se auditó ayer; el resto, sin límite
        self.assertEqual(ids[-2:], ['b1', 'b2'])

    def test_records_reach_the_catalogue_and_the_public_register(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / 'data').mkdir()
            (tree / 'assets/reading-covers').mkdir(parents=True)
            book = {**BOOK, 'portada_fuente_url': 'https://www.todostuslibros.com/x.jpg', 'portada_local': '/assets/reading-covers/isbn-9788498382372.webp'}
            (tree / 'data/reading-catalogue.json').write_text(json.dumps({'libros': [book]}), encoding='utf-8')
            record = audit_book(book, lambda url: PAGE, '2026-11-03')
            stats = audit.apply_records(tree, {'lib-1': record}, 'davidporto-21', fetch_bytes=lambda url: b'img',
                                        convert=lambda raw: (b'big', b'small', (800, 1200)))
            self.assertEqual(stats, {'formats_added': 3, 'covers_replaced': 1, 'synopses_added': 0, 'ratings': 0})
            saved = json.loads((tree / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros'][0]
            self.assertTrue(saved['portada_sustituida'])
            self.assertEqual((tree / 'assets/reading-covers/isbn-9788498382372-320.webp').read_bytes(), b'small')
            public = json.loads((tree / 'data/reading-amazon-audit.json').read_text(encoding='utf-8'))['libros']['lib-1']
            self.assertEqual((public['faltan'], public['portada']), ([], 'amazon'))
            self.assertEqual(public['mostrados'], ['tapa-blanda', 'ebook', 'audiolibro'])

    def test_amazon_stars_are_read_from_the_page_already_downloaded(self):
        self.assertEqual(page_rating(STARS), {'puntuacion': 4.6, 'numero_valoraciones': 12345})
        # Variantes: recuento solo en el texto, una sola valoración, sin título en acrPopover.
        self.assertEqual(page_rating(STARS.replace(' aria-label="12.345 valoraciones"', '').replace('(12.345)', '12.345 valoraciones')),
                         {'puntuacion': 4.6, 'numero_valoraciones': 12345})
        self.assertEqual(page_rating(STARS.replace('12.345', '1')), {'puntuacion': 4.6, 'numero_valoraciones': 1})
        self.assertEqual(page_rating(STARS.replace(' title="4,6 de 5 estrellas"', '')), {'puntuacion': 4.6, 'numero_valoraciones': 12345})
        # Novedad sin valoraciones, o nota imposible: no hay nota.
        self.assertIsNone(page_rating(PAGE))
        self.assertIsNone(page_rating(STARS.replace('4,6 de 5', '7 de 5').replace('4,6', '7')))
        record = audit_book({**BOOK}, lambda url: PAGE + STARS, '2026-11-03')
        self.assertEqual(record['valoracion'], {'puntuacion': 4.6, 'numero_valoraciones': 12345})
        self.assertNotIn('valoracion', audit_book({**BOOK}, lambda url: PAGE, '2026-11-03'))

    def test_amazon_stars_reach_the_market_without_touching_other_sources(self):
        book = {**BOOK, 'portada_fuente_url': 'https://www.penguinlibros.com/c.jpg'}
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with(tmp, [book, {**BOOK, 'id': 'lib-2'}])
            (tree / 'assets').mkdir(exist_ok=True)
            goodreads = {'libro_id': 'lib-1', 'puntuacion': 3.9, 'numero_valoraciones': 80, 'fuente': 'goodreads',
                         'url': 'https://www.goodreads.com/book/show/1-x', 'actualizado_en': '2026-11-01T00:00:00Z',
                         'caduca_en': '2026-12-01T00:00:00Z'}
            old = {**goodreads, 'fuente': 'amazon', 'puntuacion': 4.0, 'url': 'https://www.amazon.es/dp/8498382378'}
            (tree / 'assets/reading-market.json').write_text(json.dumps({'schema_version': 1, 'offers': [], 'ratings': [goodreads, old]}), encoding='utf-8')
            record = audit_book(book, lambda url: PAGE + STARS, '2026-11-03')
            unrated = audit_book(book, lambda url: PAGE, '2026-11-03')
            stats = audit.apply_records(tree, {'lib-1': record, 'lib-2': unrated}, 'davidporto-21',
                                        fetch_bytes=lambda url: b'img', convert=lambda raw: (b'big', b'small', (800, 1200)))
            self.assertEqual(stats['ratings'], 1)
            ratings = json.loads((tree / 'assets/reading-market.json').read_text(encoding='utf-8'))['ratings']
            self.assertEqual(ratings[0], goodreads)
            self.assertEqual(ratings[1:], [{'libro_id': 'lib-1', 'puntuacion': 4.6, 'numero_valoraciones': 12345, 'fuente': 'amazon',
                                            'url': 'https://www.amazon.es/dp/8498382378?tag=davidporto-21#customerReviews',
                                            'actualizado_en': '2026-11-03T00:00:00Z', 'caduca_en': '2026-12-03T00:00:00Z'}])

    def tree_with(self, tmp, books):
        tree = Path(tmp)
        (tree / 'data').mkdir()
        (tree / 'assets/reading-covers').mkdir(parents=True)
        (tree / 'data/reading-catalogue.json').write_text(json.dumps({'libros': books}), encoding='utf-8')
        return tree

    def test_cover_follows_the_book_in_main_not_the_kind_stored_in_the_record(self):
        # Registros del 04-07/11: la tipográfica de la ingesta de Amazon quedó como «editorial» y nunca se sustituía.
        typographic = {**BOOK, 'portada_fuente_url': 'https://www.amazon.es/dp/8498382378',
                       'autorizacion_o_base_uso': 'Portada tipográfica propia generada con los datos bibliográficos',
                       'portada_local': '/assets/reading-covers/isbn-9788498382372.webp'}
        editorial = {**BOOK, 'id': 'lib-2', 'portada_fuente_url': 'https://www.penguinlibros.com/c.jpg',
                     'autorizacion_o_base_uso': 'Cubierta proporcionada en la ficha oficial de la edición',
                     'portada_local': '/assets/reading-covers/isbn-9788498382373.webp'}
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with(tmp, [typographic, editorial])
            record = {**audit_book(typographic, lambda url: PAGE, '2026-11-03'), 'portada': 'editorial'}
            stats = audit.apply_records(tree, {'lib-1': record, 'lib-2': record}, 'davidporto-21', fetch_bytes=lambda url: b'img',
                                        convert=lambda raw: (b'big', b'small', (800, 1200)))
            self.assertEqual(stats['covers_replaced'], 1)
            saved = {b['id']: b for b in json.loads((tree / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']}
            self.assertTrue(saved['lib-1']['portada_sustituida'])
            self.assertTrue(saved['lib-1']['autorizacion_o_base_uso'].startswith('Cubierta de la edición tomada de su ficha de Amazon'))
            self.assertNotIn('portada_sustituida', saved['lib-2'])
            self.assertFalse((tree / 'assets/reading-covers/isbn-9788498382373.webp').exists())
            public = json.loads((tree / 'data/reading-amazon-audit.json').read_text(encoding='utf-8'))['libros']
            self.assertEqual((public['lib-1']['portada'], public['lib-2']['portada']), ('amazon', 'editorial'))

    def test_cover_cap_goes_to_the_books_closest_to_today(self):
        dates = {'lib-far': '2024-03-01', 'lib-today': '2026-11-07', 'lib-month': '2026-12', 'lib-none': ''}
        books = [{**BOOK, 'id': i, 'fecha_publicacion': d, 'portada_fuente_url': 'https://www.todostuslibros.com/x',
                  'portada_local': f'/assets/reading-covers/{i}.webp'} for i, d in dates.items()]
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with(tmp, books)
            record = audit_book(books[0], lambda url: PAGE, '2026-11-03')
            stats = audit.apply_records(tree, {i: record for i in dates}, 'davidporto-21', fetch_bytes=lambda url: b'img',
                                        convert=lambda raw, n=iter(range(99)): (b'big%d' % next(n), b'small', (800, 1200)),
                                        today=datetime(2026, 11, 8).date(), covers=2)
            self.assertEqual(stats['covers_replaced'], 2)
            saved = json.loads((tree / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']
            self.assertEqual(sorted(b['id'] for b in saved if b.get('portada_sustituida')), ['lib-month', 'lib-today'])


if __name__ == '__main__':
    unittest.main()
