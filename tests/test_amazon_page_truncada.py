"""Una página de Amazon cortada es un fallo de red de ese libro, no una excepción que tumba la noche (#1312).

gzip.decompress de un cuerpo truncado lanza EOFError y http.client IncompleteRead; los barridos solo atrapan
OSError/ValueError libro a libro, así que salían de market_refresh y la carga perdía su punto de guardado.
"""
import gzip
import http.client
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import reading_amazon_market as market  # noqa: E402


class Respuesta:
    def __init__(self, body=b'', error=None):
        self.body, self.error, self.headers = body, error, {'Content-Encoding': 'gzip'}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, limit):
        if self.error:
            raise self.error
        return self.body[:limit]


class PaginaTruncada(unittest.TestCase):
    def leer(self, respuesta):
        with patch.object(market, 'urlopen', return_value=respuesta), patch.object(market.time, 'sleep'):
            return market.fetch_amazon_page('https://www.amazon.es/dp/8400000000')

    def test_gzip_cortado_es_oserror(self):
        cortado = gzip.compress(b'<html>' + b'x' * 5000 + b'</html>')[:40]
        with self.assertRaises(OSError):
            self.leer(Respuesta(cortado))

    def test_lectura_incompleta_es_oserror(self):
        with self.assertRaises(OSError):
            self.leer(Respuesta(error=http.client.IncompleteRead(b'abc', 100)))
        with patch.object(market, 'urlopen', return_value=Respuesta(error=http.client.IncompleteRead(b'', 9))):
            with self.assertRaises(OSError):
                market.fetch_amazon_image('https://m.media-amazon.com/images/I/x.jpg')

    def test_pagina_entera_se_lee(self):
        self.assertEqual(self.leer(Respuesta(gzip.compress('<html>ñ</html>'.encode()))), '<html>ñ</html>')


if __name__ == '__main__':
    unittest.main()
