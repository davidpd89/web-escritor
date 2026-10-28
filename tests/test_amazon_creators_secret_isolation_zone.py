import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_amazon_market import CreatorsPrices, refresh_offers


class AmazonSecretIsolation(unittest.TestCase):
    def test_authentication_error_does_not_expose_credentials(self):
        secret = 'PRIVATE_CLIENT_SECRET_TEST'
        client = CreatorsPrices('CLIENT_ID_TEST', secret, 'davidporto-21')
        url = 'https://api.amazon.co.uk/auth/o2/token'
        error = HTTPError(url, 401, 'Unauthorized', {}, None)
        with patch('reading_amazon_market.urlopen', side_effect=error):
            with self.assertRaises(RuntimeError) as caught:
                client.post(url, {'client_secret': secret})
        self.assertNotIn(secret, str(caught.exception), 'Amazon: el error contiene client_secret')
        self.assertNotIn('CLIENT_ID_TEST', str(caught.exception), 'Amazon: el error contiene client_id')

    def test_refresh_failure_does_not_publish_provider_token(self):
        token = 'PRIVATE_ACCESS_TOKEN_TEST'
        book = {'id': 'lib-0001', 'estado': 'publicado', 'isbn13': '9788498382372'}
        def unavailable(_):
            raise RuntimeError('Amazon Creators HTTP 401')
        result, stats = refresh_offers(
            {'libros': [book]}, {'offers': []}, unavailable,
            'davidporto-21', datetime(2026, 10, 26, tzinfo=timezone.utc), budget=1
        )
        output = json.dumps({'result': result, 'stats': stats})
        self.assertNotIn(token, output)
        self.assertNotIn('client_secret', output)
        self.assertNotIn('Authorization', output)
        self.assertEqual(stats['attempted'], 1)
        self.assertEqual(stats['status'], 'provider_unavailable')


if __name__ == '__main__':
    unittest.main()
