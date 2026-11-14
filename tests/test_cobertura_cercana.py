import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

import cobertura_cercana as cc  # noqa: E402

HOST = 'https://www.todostuslibros.com/libros/'


def pagina(*isbns):
    return ''.join(f'<a href="{HOST}libro-{i}_{i[:3]}-{i[3:5]}-{i[5:]}">x</a>' for i in isbns)


def ficha(fecha):
    return f'<dt>Fecha publicación</dt><dd>{fecha}</dd>' if fecha else ''


class LeerListado(unittest.TestCase):
    def fetch_de(self, paginas, fechas):
        def fetch(url):
            if '/categoria/' in url:
                n = int(url.rsplit('page=', 1)[1])
                return pagina(*paginas[n - 1]) if n <= len(paginas) else ''
            isbn = url.rsplit('_', 1)[1].replace('-', '')
            return ficha(fechas.get(isbn))
        return fetch

    def test_pagina_entera_dentro_y_frontera_ficha_a_ficha(self):
        a, b, c, d = '9788400000103', '9788400000202', '9788400000301', '9788400000400'
        fechas = {a: '15-11-2026', b: '16-11-2026', c: '16-11-2026', d: '20-11-2026'}
        fetch = self.fetch_de([[a, b], [c, d]], fechas)
        dentro = cc.leer_listado(fetch, 'x', 'proximas_apariciones', 'asc', '2026-11-14', '2026-11-16')
        self.assertEqual(set(dentro), {a, b, c})

    def test_pagina_con_primer_extremo_fuera_va_ficha_a_ficha(self):
        a, b = '9788400000103', '9788400000202'
        fetch = self.fetch_de([[a, b]], {a: '15-11-2026', b: '16-11-2026'})
        self.assertEqual(set(cc.leer_listado(fetch, 'x', 'proximas_apariciones', 'asc', '2026-11-16', '2026-11-18')), {b})

    def test_listado_que_repite_pagina_se_corta(self):
        a = '9788400000103'
        base, pedidas = self.fetch_de([[a], [a], [a]], {a: '14-11-2026'}), []

        def fetch(url):
            pedidas.append(url)
            return base(url)
        self.assertEqual(set(cc.leer_listado(fetch, 'x', 'novedades', 'desc', '2026-11-14', '2026-11-16')), {a})
        self.assertEqual(sum('/categoria/' in u for u in pedidas), 2)  # la 3 no se pide: la 2 repite la 1


class Clasificar(unittest.TestCase):
    def test_situaciones(self):
        isbn = '9788400000103'
        asin = '8400000102'
        vacio = ({}, {}, {})
        self.assertEqual(cc.clasificar(isbn, {isbn}, *vacio, '2026-11-14')[0], 'en_la_web')
        self.assertEqual(cc.clasificar(isbn, set(), {}, {}, {isbn: 'Amazon no lo tiene'}, '2026-11-14'),
                         ('descartado', 'Amazon no lo tiene'))
        pend = {asin: {'motivo': 'aplazado por cupo de altas'}}
        self.assertEqual(cc.clasificar(isbn, set(), {}, pend, {}, '2026-11-14')[0], 'aplazado_por_cupo')
        cola = {isbn: {'intentos': 1, 'siguiente': '2026-11-15'}}
        self.assertEqual(cc.clasificar(isbn, set(), cola, {}, {}, '2026-11-14')[0], 'en_cola')
        self.assertEqual(cc.clasificar(isbn, set(), *vacio, '2026-11-14')[0], 'sin_explicar')

    def test_979_se_sigue_por_isbn13_y_cuarentena(self):
        isbn = '9791399282313'  # sin ISBN-10: su ASIN es B0…
        pend = cc.pendientes_por_isbn({'B0ABCDEFGH': {'motivo': 'aplazado por cupo de altas', 'isbn13': isbn}})
        self.assertEqual(cc.clasificar(isbn, set(), {}, pend, {}, '2026-11-14')[0], 'aplazado_por_cupo')
        self.assertEqual(cc.clasificar(isbn, set(), {}, pend, {isbn: 'Amazon no lo tiene'}, '2026-11-14')[0],
                         'aplazado_por_cupo')  # volvió a la cola: manda lo activo, no el descarte antiguo
        self.assertEqual(cc.clasificar(isbn, set(), {}, {}, {}, '2026-11-14', {isbn: 'sinopsis'}),
                         ('en_cuarentena', 'sinopsis'))


if __name__ == '__main__':
    unittest.main()
