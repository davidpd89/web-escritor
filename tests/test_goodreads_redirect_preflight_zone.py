import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_goodreads import GoodreadsPublic


class GoodreadsRedirectPreflight(unittest.TestCase):
    def test_foreign_redirect_is_rejected_before_following(self):
        origin = 'https://www.goodreads.com/book/isbn/9788498382372'
        destination = 'https://example.org/collect'
        attempts = []

        class RedirectResponse:
            status = 302
            code = 302
            headers = {'Location': destination}
            url = origin
            def info(self):
                return self.headers
            def geturl(self):
                return self.url
            def close(self):
                pass

        class Transport:
            def __call__(self, request, timeout=None):
                attempts.append(request.full_url)
                if request.full_url == origin:
                    raise HTTPError(origin, 302, 'Found', {'Location': destination}, None)
                raise AssertionError('Solicitud enviada a un tercero: ' + request.full_url)

        class RedirectingHandler(HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                return super().http_error_302(req, fp, code, msg, headers)

        with patch('reading_goodreads.urlopen', side_effect=Transport()):
            with self.assertRaises((RuntimeError, ValueError, HTTPError)):
                GoodreadsPublic(delay=0).fetch(origin)
        self.assertEqual(attempts, [origin], 'Goodreads: se siguió una redirección hacia un origen ajeno')

    def test_default_transport_uses_automatic_redirect_handler(self):
        # fetch() solo reintenta con backoff; el transporte y la validación del destino viven en fetch_once().
        import inspect
        import reading_goodreads
        source = inspect.getsource(reading_goodreads.GoodreadsPublic.fetch_once)
        self.assertIn('urlopen(', source)
        self.assertIn('final_url', source)
        self.assertNotIn('HTTPRedirectHandler', source)


if __name__ == '__main__':
    unittest.main()
