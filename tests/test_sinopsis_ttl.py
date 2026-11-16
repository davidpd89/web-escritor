"""Sinopsis de las altas de Amazon desde la ficha de todostuslibros, solo si la página es de ese ISBN exacto."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import sinopsis_google_books as gb
from reading_ttl_source import ttl_sinopsis

HOY = date(2026, 11, 16)
TEXTO = ('<p>Una joven cartógrafa descubre que los mapas de su ciudad mienten y que alguien borra calles enteras '
         'cada noche para ocultar un secreto antiguo.</p><p>Con la ayuda de un archivero desconfiado, tendrá que '
         'elegir entre la verdad y la vida que conocía.</p>')


def ficha(isbn, sinopsis=TEXTO, host='www.todostuslibros.com'):
    return (f'<html><head><link rel="canonical" href="https://{host}/libros/los-mapas_{isbn}"></head><body>'
            f'<div class="collapse" id="collapseSynopsis">{sinopsis}</div></body></html>')


def libro(isbn, fecha='2026-11-16'):
    return {'isbn13': isbn, 'estado': 'publicado', 'fecha_publicacion': fecha}


class SinopsisTTLTest(unittest.TestCase):
    def test_rellena_con_la_ficha_del_mismo_isbn(self):
        cat = {'libros': [libro('9788491058571')]}
        n = gb.rellenar(cat, ficha, {}, HOY, extraer=ttl_sinopsis)
        b = cat['libros'][0]
        self.assertEqual(n, 1)
        self.assertEqual(b['sinopsis_fuente_url'], 'https://www.todostuslibros.com/libros/los-mapas_9788491058571')
        self.assertIn('cartógrafa', b['sinopsis_completa'])
        self.assertNotIn('<p>', b['sinopsis_completa'])

    def test_otra_ficha_otro_host_o_sin_ficha_no_valen_y_esperan(self):
        cat = {'libros': [libro('9788491058571'), libro('9788408331148'), libro('9788402432148')]}
        respuestas = {'9788491058571': ficha('9788491058779'),
                      '9788408331148': ficha('9788408331148', host='otra.example'),
                      '9788402432148': ''}
        intentos = {}
        self.assertEqual(gb.rellenar(cat, respuestas.get, intentos, HOY, extraer=ttl_sinopsis), 0)
        self.assertEqual(set(intentos), set(respuestas))

    def test_ficha_sin_sinopsis_no_publica_nada(self):
        cat = {'libros': [libro('9788491058571')]}
        gb.rellenar(cat, lambda i: ficha(i, sinopsis=''), {}, HOY, extraer=ttl_sinopsis)
        self.assertNotIn('sinopsis_completa', cat['libros'][0])

    def test_web_caida_para_sin_marcar(self):
        cat = {'libros': [libro('9788491058571')]}
        intentos = {}
        self.assertEqual(gb.rellenar(cat, lambda i: None, intentos, HOY, extraer=ttl_sinopsis), 0)
        self.assertEqual(intentos, {})


    def test_sin_resultado_reintenta_a_los_dias_dados_y_tras_dos_fallos_queda_pendiente(self):
        cat = {'libros': [libro('9788491058571'), libro('9788408331148')]}
        intentos, fallos = {}, {}
        gb.rellenar(cat, lambda i: '', intentos, HOY, extraer=ttl_sinopsis, fallos=fallos)
        self.assertEqual(intentos['9788491058571'], '2026-11-18')  # 2 días, no 30
        self.assertEqual(gb.pendientes(cat, fallos), [])  # un solo fallo: aún no
        gb.rellenar(cat, lambda i: '', intentos, date(2026, 11, 18), extraer=ttl_sinopsis, fallos=fallos)
        self.assertEqual(gb.pendientes(cat, fallos), ['9788408331148', '9788491058571'])
        cat['libros'][0]['sinopsis_breve'] = 'Ya la tiene por otra fuente.'
        self.assertEqual(gb.pendientes(cat, fallos), ['9788408331148'])
        self.assertNotIn('9788491058571', fallos)
        intentos = {}
        gb.rellenar(cat, lambda i: '', intentos, HOY, extraer=ttl_sinopsis, reintento_dias=7)
        self.assertEqual(intentos['9788408331148'], '2026-11-23')


if __name__ == '__main__':
    unittest.main()
