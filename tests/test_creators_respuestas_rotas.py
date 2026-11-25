"""R3-03/04/11 de GPT (25/11): el cliente Creators solo deja salir errores con tipo (RuntimeError y sus hijas).

Los llamantes del catálogo Amazon capturan RuntimeError (NotFound/AccessDenied/Unavailable); un ValueError, KeyError,
TypeError o IncompleteRead suelto tumbaba la fase entera. Fuzz con semilla fija: cuerpos 200 rotos, errores HTTP con
JSON raro y respuestas de autenticación sin token.
"""
import http.client
import io
import json
import random
import sys
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import reading_amazon_market as m  # noqa: E402


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Cortada:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, *a):
        raise http.client.IncompleteRead(b'{"items": [', 500)


def http_error(code, cuerpo):
    return HTTPError('https://x', code, 'x', {}, io.BytesIO(cuerpo))


def cuerpos(rng, n=150):
    fijos = [b'', b'<html>Error</html>', b'{"a":', b'null', b'[]', b'"x"', b'1', b'\xff\xfe\x00', b'{"a": NaN}']
    for c in fijos:
        yield c
    for _ in range(n):
        base = json.dumps({'items': [{'asin': 'B0' + str(rng.randrange(10**8))}]}).encode()
        corte = rng.randrange(len(base) + 1)
        yield base[:corte] if rng.random() < .6 else bytes(rng.randrange(256) for _ in range(rng.randrange(40)))


class CreatorsRespuestasRotas(unittest.TestCase):
    def setUp(self):
        self.cliente = m.CreatorsPrices('id', 'secret', 'tag-21')
        for p in (mock.patch.object(m.time, 'sleep'), ):
            p.start()
            self.addCleanup(p.stop)

    def llamar(self, efecto):
        with mock.patch.object(m, 'urlopen', side_effect=efecto):
            try:
                return self.cliente.post('https://x', {}, retries=1)
            except RuntimeError as exc:
                return exc

    def test_200_con_cuerpo_roto_es_unavailable(self):
        rng = random.Random(20261125)
        for cuerpo in cuerpos(rng):
            try:
                json.loads(cuerpo)
                continue  # JSON válido: no es el caso
            except ValueError:
                pass
            with self.subTest(cuerpo=cuerpo[:30]):
                self.assertIsInstance(self.llamar(lambda *a, c=cuerpo, **k: Resp(c)), m.Unavailable)

    def test_cuerpo_cortado_a_mitad_de_lectura_es_unavailable(self):
        self.assertIsInstance(self.llamar(lambda *a, **k: Cortada()), m.Unavailable)

    def test_json_valido_que_no_es_objeto_es_error_con_tipo(self):
        for cuerpo in (b'null', b'[]', b'"x"', b'1'):
            with self.subTest(cuerpo=cuerpo):
                self.assertIsInstance(self.llamar(lambda *a, c=cuerpo, **k: Resp(c)), RuntimeError)

    def test_errores_http_con_json_raro_salen_con_tipo(self):
        rng = random.Random(7)
        raros = [None, 1, {}, 'x', [None, 1, {'code': None}], [{'code': 'AssociateNotEligible'}]]
        for code in (400, 403, 404, 429, 500, 503):
            for errores in raros:
                for mensaje in (None, 1, 'Request rejected', {'a': 1}):
                    cuerpo = json.dumps({'message': mensaje, 'errors': errores,
                                         'retryAfterSeconds': rng.choice([None, 'x', -1, 1e9])}).encode()
                    with self.subTest(code=code, errores=errores, mensaje=mensaje):
                        def lanza(*a, c=code, b=cuerpo, **k):
                            raise http_error(c, b)
                        self.assertIsInstance(self.llamar(lanza), RuntimeError)

    def test_403_no_elegible_se_sigue_reconociendo(self):
        def lanza(*a, **k):
            raise http_error(403, json.dumps({'errors': [{'code': 'AssociateNotEligible'}]}).encode())
        self.assertIsInstance(self.llamar(lanza), m.AccessDenied)

    def test_autenticacion_sin_token_es_unavailable_y_acaba_cortando(self):
        for data in ({}, {'access_token': None}, {'access_token': ''}, {'access_token': 123}, {'access_token': '  '}):
            with self.subTest(data=data):
                cliente = m.CreatorsPrices('id', 'secret', 'tag-21')
                with mock.patch.object(cliente, 'post', return_value=data):
                    with self.assertRaises(m.Unavailable):
                        cliente.headers()
        cliente = m.CreatorsPrices('id', 'secret', 'tag-21')
        with mock.patch.object(m, 'urlopen', side_effect=lambda *a, **k: Resp(b'{"expires_in": 3600}')):
            for _ in range(m.CORTE):
                with self.assertRaises(m.Unavailable):
                    cliente.headers()
        self.assertTrue(cliente.caido, 'un token que nunca llega corta como una caída, no repite login por libro')


if __name__ == '__main__':
    unittest.main()
