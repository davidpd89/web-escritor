"""Contratos sintéticos para fuentes gratuitas; SIN peticiones reales."""
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_free_prices import cents, google_ebook_offer, penguin_offer, refresh_penguin, refresh_google_ebooks

NOW = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)
ISBN = '9788401039560'
URL = 'https://www.penguinlibros.com/es/libros-de-fantasia/635029-libro-otros-mundos-el-talisman-3-' + ISBN
BOOK = {
    'id': 'isbn-' + ISBN, 'isbn13': ISBN, 'titulo': 'Otros mundos (El Talismán 3)',
    'autores': ['Stephen King', 'Peter Straub'], 'formato_edicion': 'tapa-dura',
    'fuente_bibliografica_url': URL, 'estado': 'publicado'
}
EDITION = {'isbn13': ISBN, 'titulo': BOOK['titulo'], 'autores': BOOK['autores'],
           'formato_edicion': 'tapa-dura'}


def product(**updates):
    entry = {'reference': ISBN, 'price_amount': 25.49, 'regular_price_amount': 26.83}
    entry.update(updates)
    return '<div data-product="' + json.dumps(entry).replace('"', '&quot;') + '"></div>'


def google_volume(country='ES', isbn=ISBN, price=8.99):
    return {'volumeInfo': {'title': BOOK['titulo'], 'authors': ['Stephen King', 'Peter Straub'],
            'industryIdentifiers': [{'type': 'ISBN_13', 'identifier': isbn}]},
            'saleInfo': {'country': country, 'saleability': 'FOR_SALE', 'isEbook': True,
                'retailPrice': {'amount': price, 'currencyCode': 'EUR'},
                'buyLink': 'https://books.google.com/books?id=example'}}


class FreePriceTests(unittest.TestCase):
    def test_currency_parser_strict(self):
        self.assertEqual(cents('25,49 €'), 2549)
        self.assertEqual(cents(25.49), 2549)
        for value in (True, False, None, '25 €', '25,4', '25,490', 'nan', '25,49 USD', -1):
            with self.subTest(value=value):
                self.assertIsNone(cents(value))

    @patch('reading_free_prices.penguin_edition', return_value=EDITION)
    def test_official_same_isbn_price_and_reference(self, _mock):
        result = penguin_offer(BOOK, product(), NOW)
        self.assertEqual(result['fuente'], 'penguin_libros')
        self.assertEqual(result['precio_centimos'], 2549)
        self.assertEqual(result['precio_referencia_centimos'], 2683)
        self.assertEqual(result['caduca_en'], '2026-10-22T12:00:00Z')
        self.assertEqual(result['url'], URL)

    @patch('reading_free_prices.penguin_edition', return_value=EDITION)
    def test_absent_price_does_not_scrape_random_amounts(self, _mock):
        self.assertIsNone(penguin_offer(BOOK, product(price_amount=None), NOW))
        self.assertIsNone(penguin_offer(BOOK, product(reference='9788401039546'), NOW))
        self.assertIsNone(penguin_offer(BOOK, product(price_amount='27,95 USD'), NOW))

    @patch('reading_free_prices.penguin_edition', return_value=EDITION)
    def test_rejects_other_merchant(self, _mock):
        alien = dict(BOOK, fuente_bibliografica_url='https://www.amazon.es/dp/B000000000')
        self.assertIsNone(penguin_offer(alien, product(), NOW))

    @patch('reading_free_prices.penguin_edition', return_value=EDITION)
    def test_rejects_wrong_author_or_format(self, _mock):
        self.assertIsNone(penguin_offer(dict(BOOK, autores=['Otra Persona']), product(), NOW))
        self.assertIsNone(penguin_offer(dict(BOOK, formato_edicion='ebook'), product(), NOW))

    def test_google_books_price_requires_real_same_isbn_ebook_in_spain(self):
        ebook = dict(BOOK, formato_edicion='ebook')
        offer = google_ebook_offer(ebook, {'items': [google_volume()]}, NOW)
        self.assertEqual(offer['precio_centimos'], 899)
        self.assertEqual(offer['fuente'], 'google_play_libros')
        self.assertIsNone(google_ebook_offer(BOOK, {'items': [google_volume()]}, NOW))
        self.assertIsNone(google_ebook_offer(ebook, {'items': [google_volume(country='US')]}, NOW))
        self.assertIsNone(google_ebook_offer(ebook, {'items': [google_volume(isbn='9788401039546')]}, NOW))
        copy = google_volume()
        copy['saleInfo']['isEbook'] = False
        self.assertIsNone(google_ebook_offer(ebook, {'items': [copy]}, NOW))
        copy['saleInfo']['isEbook'] = True
        copy['saleInfo']['retailPrice']['currencyCode'] = 'USD'
        self.assertIsNone(google_ebook_offer(ebook, {'items': [copy]}, NOW))

    @patch('reading_free_prices.penguin_edition', return_value=EDITION)
    def test_refresh_is_idempotent_under_failed_provider(self, _mock):
        previous = {'schema_version': 1, 'offers': []}
        dataset = {'libros': [BOOK]}
        result, stats = refresh_penguin(dataset, previous, lambda _: product(), NOW)
        self.assertEqual(stats['actualizados'], 1)
        self.assertEqual(len(result['offers']), 1)
        failed, failures = refresh_penguin(dataset, result, lambda _: (_ for _ in ()).throw(TimeoutError()), NOW)
        self.assertEqual(failures['consultados'], 1)
        self.assertEqual(failed['offers'], result['offers'])

    def test_google_is_optional_and_no_call_for_paper_books(self):
        result, stats = refresh_google_ebooks({'libros': [BOOK]},
            {'schema_version': 1, 'offers': []},
            lambda isbn: self.fail('Paper ISBN should not be queried as ebook'), NOW)
        self.assertEqual(stats['consultados'], 0)
        self.assertEqual(result['offers'], [])

    def test_google_provider_error_halts_without_renewing_old_data(self):
        ebook = dict(BOOK, formato_edicion='ebook')
        old = {'schema_version': 1, 'offers': [
            {'libro_id': ebook['id'], 'fuente': 'google_play_libros',
             'actualizado_en': '2026-10-21T09:00:00Z',
             'caduca_en': '2026-10-22T09:00:00Z'}]}
        calls = []
        def denied(isbn):
            calls.append(isbn)
            raise RuntimeError('Google Books HTTP 503')
        updated, stats = refresh_google_ebooks({'libros': [ebook]}, old, denied, NOW)
        self.assertEqual(calls, [ISBN])
        self.assertEqual(stats['consultados'], 1)
        self.assertEqual(updated['offers'], old['offers'])

    def test_no_network_when_budget_zero(self):
        calls = []
        result, stats = refresh_penguin({'libros': [BOOK]}, {'offers': [], 'schema_version': 1},
                                        lambda _: calls.append(True), NOW, budget=0)
        self.assertEqual(calls, [])
        self.assertEqual(result['offers'], [])
        self.assertEqual(stats['consultados'], 0)


if __name__ == '__main__':
    unittest.main()
