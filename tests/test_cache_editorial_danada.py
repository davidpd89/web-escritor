"""R3-06 de GPT (25/11): una entrada de la caché editorial dañada se trata como fallo de caché y se vuelve a pedir.

Antes el JSON de metadatos roto (runner muerto mientras lo escribía, caché de Actions restaurada a medias) hacía
fallar la fuente en cada carga aunque la web respondiera bien.
"""
import hashlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_editorial_sources import CachedHTTP  # noqa: E402

URL = 'https://www.penguinlibros.com/es/libro-9780140328721'


class Respuesta(io.BytesIO):
    url = URL
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class CacheEditorialDanada(unittest.TestCase):
    def test_metadatos_rotos_se_piden_de_nuevo_y_se_reparan(self):
        for roto in ('{"retrieved_at":', '', 'null', '[]', '{}', '{"retrieved_at": "ayer"}', '{"retrieved_at": null}'):
            with self.subTest(roto=roto), tempfile.TemporaryDirectory() as tmp:
                http = CachedHTTP(Path(tmp), ['www.penguinlibros.com'], delay=0, now=lambda: 1000.0)
                key = hashlib.sha256(URL.encode()).hexdigest()
                (Path(tmp) / (key + '.body')).write_bytes(b'viejo')
                (Path(tmp) / (key + '.json')).write_text(roto, encoding='utf-8')
                with mock.patch.object(http.opener, 'open', return_value=Respuesta(b'nuevo')) as abrir:
                    self.assertEqual(http.get(URL, robots=False), b'nuevo')
                    self.assertEqual(abrir.call_count, 1)
                    self.assertEqual(http.get(URL, robots=False), b'nuevo', 'la entrada queda reparada')
                    self.assertEqual(abrir.call_count, 1)
                self.assertFalse(list(Path(tmp).glob('*.tmp')), 'sin temporales sueltos')


if __name__ == '__main__':
    unittest.main()
