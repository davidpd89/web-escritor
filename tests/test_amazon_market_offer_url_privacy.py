import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_amazon_market import select_offers

ASIN = 'B08CYCPBZN'
TAG = 'davidporto-21'
NOW = datetime(2026, 10, 21, tzinfo=timezone.utc)


class AmazonOfferUrlPrivacy(unittest.TestCase):
    def test_verified_offer_generates_clean_affiliate_url(self):
        book = {
            'id': 'lib-test', 'titulo': 'Coraline',
            'autores': ['Neil Gaiman'], 'isbn13': '9788498382372',
            'estado': 'publicado',
            'formatos_compra': [{'url': f'https://www.amazon.es/dp/{ASIN}?tag={TAG}', 'formato': 'ebook'}]
        }
        item = {
            'asin': ASIN,
            'itemInfo': {
                'title': {'displayValue': 'Coraline'},
                'byLineInfo': {'contributors': [{'name': 'Neil Gaiman', 'role': 'Author'}]},
                'externalIds': {},
                'classifications': {'binding': {'displayValue': 'Kindle'}}
            },
            'offersV2': {'listings': [{
                'condition': {'value': 'New'},
                'availability': {'type': 'IN_STOCK'},
                'price': {'money': {'amount': 5.99, 'currency': 'EUR'}}
            }]}
        }
        offers = select_offers(book, {'searchResult': {'items': [item]}}, TAG, NOW)
        self.assertEqual(len(offers), 1, 'Coraline: oferta Amazon verificada ausente')
        url = offers[0]['url']
        parsed = urlsplit(url)
        self.assertEqual(parsed.scheme, 'https', f'Coraline: esquema inseguro: {url}')
        self.assertEqual(parsed.netloc, 'www.amazon.es', f'Coraline: autoridad incorrecta: {url}')
        self.assertEqual(parsed.path, f'/dp/{ASIN}', f'Coraline: ASIN incorrecto: {url}')
        self.assertEqual(parse_qs(parsed.query), {'tag': [TAG]}, f'Coraline: parámetros inesperados: {url}')
        self.assertFalse(parsed.fragment, f'Coraline: fragmento inesperado: {url}')
        self.assertIsNone(parsed.username, f'Coraline: usuario incrustado: {url}')
        self.assertIsNone(parsed.password, f'Coraline: contraseña incrustada: {url}')


if __name__ == '__main__':
    unittest.main()
