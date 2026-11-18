"""P1-11: sinopsis de respaldo desde Google Books, solo con ISBN exacto, en español y con procedencia https."""
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import sinopsis_google_books as gb

HOY = date(2026, 11, 16)
TEXTO = ('<p>Una joven cartógrafa descubre que los mapas de su ciudad mienten y que alguien borra calles enteras '
         'cada noche para ocultar un secreto antiguo.</p><p>Con la ayuda de un archivero desconfiado, tendrá que '
         'elegir entre la verdad y la vida que conocía.</p>')


def volumen(isbn, idioma='es', texto=TEXTO, vid='abc123'):
    return {'items': [{'id': vid, 'volumeInfo': {'language': idioma, 'description': texto,
                                                 'industryIdentifiers': [{'type': 'ISBN_13', 'identifier': isbn}]}}]}


def libro(isbn, fecha='2026-11-16', **extra):
    return {'isbn13': isbn, 'estado': 'publicado', 'fecha_publicacion': fecha, **extra}


class HilosRevision1383Test(unittest.TestCase):
    def test_cercania_tolera_fechas_vacias_parciales_y_no_textuales(self):
        libros = [libro('9788400000001', None), libro('9788400000002', '2020-01-01'),
                  libro('9788400000003', '', fecha_publicacion_parcial='2026-11'), libro('9788400000004', 20261116)]
        orden = [b['isbn13'][-1] for b in sorted(libros, key=lambda b: gb.cercania(b, HOY))]
        self.assertEqual(orden[:2], ['3', '2'], 'el mes en curso antes que 2020; lo ilegible al final')

    def test_una_ficha_rara_no_tumba_el_lote(self):
        cat = {'libros': [libro('9788400000001'), libro('9788400000002')]}
        def extraer(respuesta, isbn):
            if isbn.endswith('1'):
                raise ValueError('Invalid IPv6 URL')
            return gb.de_google(respuesta, isbn)
        intentos = {}
        self.assertEqual(gb.rellenar(cat, volumen, intentos, HOY, extraer=extraer), 1)
        self.assertIn('9788400000001', intentos, 'se reintenta otro día')


class PlazoSinopsisTest(unittest.TestCase):
    """Ningún libro pasa 30 días sin sinopsis: a los 20 entra en la lista manual/GPT aunque Google no haya fallado."""

    def test_a_los_veinte_dias_pasa_a_mano_los_mas_antiguos_primero(self):
        cat = {'libros': [libro('9788400000001'), libro('9788400000002'), libro('9788400000003')]}
        desde = {}
        self.assertEqual(gb.pendientes(cat, {}, desde=desde, hoy=HOY), [], 'el primer día solo se anota')
        self.assertEqual(set(desde), {'9788400000001', '9788400000002', '9788400000003'})
        desde['9788400000002'] = (HOY - timedelta(days=25)).isoformat()
        desde['9788400000003'] = (HOY - timedelta(days=21)).isoformat()
        self.assertEqual(gb.pendientes(cat, {}, desde=desde, hoy=HOY), ['9788400000002', '9788400000003'])
        self.assertEqual(gb.vencidas(desde, HOY), 0)
        desde['9788400000002'] = (HOY - timedelta(days=31)).isoformat()
        self.assertEqual(gb.vencidas(desde, HOY), 1)

    def test_con_sinopsis_sale_del_registro(self):
        cat = {'libros': [libro('9788400000001')]}
        desde = {'9788400000001': '2020-01-01', '9788400000009': 'basura'}
        cat['libros'][0]['sinopsis_breve'] = 'x' * 40
        self.assertEqual(gb.pendientes(cat, {}, desde=desde, hoy=HOY), [])
        self.assertEqual(desde, {})


class SinopsisGoogleTest(unittest.TestCase):
    def test_rellena_con_isbn_exacto_y_procedencia(self):
        cat = {'libros': [libro('9788400000001')]}
        n = gb.rellenar(cat, volumen, {}, HOY)
        b = cat['libros'][0]
        self.assertEqual(n, 1)
        self.assertEqual(b['sinopsis_tipo'], 'extracto_editorial')
        self.assertEqual(b['sinopsis_fuente_url'], 'https://books.google.com/books?id=abc123')
        self.assertTrue(30 <= len(b['sinopsis_breve']) <= 700)
        self.assertTrue(60 <= len(b['sinopsis_completa']) <= 4500)
        self.assertIn('\n\n', b['sinopsis_completa'])
        self.assertNotIn('<p>', b['sinopsis_completa'])

    def test_otro_isbn_u_otro_idioma_no_valen_y_esperan_2_dias(self):
        cat = {'libros': [libro('9788400000001'), libro('9788400000002')]}
        intentos = {}
        respuestas = {'9788400000001': volumen('9788400000999'), '9788400000002': volumen('9788400000002', 'en')}
        self.assertEqual(gb.rellenar(cat, respuestas.get, intentos, HOY), 0)
        self.assertNotIn('sinopsis_breve', cat['libros'][0])
        self.assertEqual(intentos, {'9788400000001': '2026-11-18', '9788400000002': '2026-11-18'})
        llamadas = []
        gb.rellenar(cat, lambda i: llamadas.append(i) or volumen(i), intentos, HOY)
        self.assertEqual(llamadas, [], 'no se repite antes del reintento')
        gb.rellenar(cat, lambda i: llamadas.append(i) or volumen(i), intentos, date(2026, 12, 16))
        self.assertEqual(len(llamadas), 2, 'pasado el plazo se poda y se vuelve a pedir')

    def test_no_toca_lo_que_ya_tiene_sinopsis_ni_lo_no_publicado(self):
        cat = {'libros': [libro('9788400000001', sinopsis_breve='x' * 40),
                          libro('9788400000002', sinopsis_completa='y' * 80),
                          libro('9788400000003', sinopsis_tipo='resumen_propio'),
                          libro('9788400000004', estado='pendiente'),
                          libro('B0ABCDEFGH')]}
        llamadas = []
        gb.rellenar(cat, lambda i: llamadas.append(i) or volumen(i), {}, HOY)
        self.assertEqual(llamadas, [])

    def test_cercanas_primero_con_tope_y_google_caido_no_marca(self):
        cat = {'libros': [libro('9788400000001', '2020-01-01'), libro('9788400000002', '2026-11-17'),
                          libro('9788400000003', '2026-11-16')]}
        llamadas = []
        gb.rellenar(cat, lambda i: llamadas.append(i) or volumen(i), {}, HOY, max_libros=2)
        self.assertEqual(llamadas, ['9788400000003', '9788400000002'])
        intentos = {}
        self.assertEqual(gb.rellenar(cat, lambda i: None, intentos, HOY), 0)
        self.assertEqual(intentos, {}, 'una caída de Google no cuenta como intento')

    def test_descripcion_corta_o_vacia_no_se_publica(self):
        cat = {'libros': [libro('9788400000001')]}
        gb.rellenar(cat, lambda i: volumen(i, texto='Novela.'), {}, HOY)
        self.assertNotIn('sinopsis_breve', cat['libros'][0])


if __name__ == '__main__':
    unittest.main()
