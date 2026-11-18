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


class Frontera(unittest.TestCase):
    @staticmethod
    def con_control(doce):
        return doce + str(-sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(doce)) % 10)

    def leer(self, fechas, orden, desde, hasta):
        isbns = [self.con_control(f'97884000{n:04d}') for n in range(1, 33)]  # una página de 32 tarjetas
        tabla, pedidas = dict(zip(isbns, fechas)), []

        def fetch(url):
            if '/categoria/' in url:
                return pagina(*isbns) if url.endswith('page=1') else ''
            pedidas.append(url)
            return ficha(tabla[url.rsplit('_', 1)[1].replace('-', '')])
        dentro = cc.leer_listado(fetch, 'x', 'proximas_apariciones', orden, desde, hasta)
        return isbns, dentro, len(pedidas)

    def test_el_corte_se_busca_por_biseccion(self):
        fechas = ['17-11-2026'] * 9 + ['18-11-2026'] * 4 + ['25-11-2026'] * 40
        isbns, dentro, fichas = self.leer(fechas, 'asc', '2026-11-16', '2026-11-18')
        self.assertEqual(set(dentro), set(isbns[:13]))
        self.assertLess(fichas, len(isbns) / 2)

    def test_descendente_y_tramo_en_medio(self):
        fechas = ['25-11-2026'] * 3 + ['18-11-2026'] * 5 + ['10-11-2026'] * 40
        isbns, dentro, _fichas = self.leer(fechas, 'desc', '2026-11-16', '2026-11-18')
        self.assertEqual(set(dentro), set(isbns[3:8]))

    def test_fecha_ilegible_vuelve_a_ficha_a_ficha(self):
        fechas = ['17-11-2026', '', '17-11-2026'] + [''] * 20 + ['25-11-2026'] * 40
        isbns, dentro, fichas = self.leer(fechas, 'asc', '2026-11-16', '2026-11-18')
        self.assertEqual(set(dentro), {isbns[0], isbns[2]})
        self.assertEqual(fichas, len(isbns))  # todas, y ninguna dos veces


class PresupuestoTests(unittest.TestCase):
    A, B, C, D = '9788400000103', '9788400000202', '9788400000301', '9788400000400'
    FECHAS = {A: '15-11-2026', B: '15-11-2026', C: '16-11-2026', D: '16-11-2026'}
    LISTADOS = [('uno', 'novedades', 'desc'), ('dos', 'novedades', 'desc')]

    def fuente(self, pedidas):
        """Dos categorías de dos páginas cada una, todas dentro de la ventana."""
        paginas = {'uno': [[self.A], [self.B]], 'dos': [[self.C], [self.D]]}

        def get(url):
            pedidas.append(url)
            if '/categoria/' in url:
                categoria = next(c for c in paginas if f'/{c}' in url)
                n = int(url.rsplit('page=', 1)[1])
                return pagina(*paginas[categoria][n - 1]) if n <= 2 else ''
            return ficha(self.FECHAS[url.rsplit('_', 1)[1].replace('-', '')])
        return get

    def recoger(self, presupuesto):
        return cc.recoger(presupuesto.fetch, self.LISTADOS, '2026-11-14', '2026-11-16')

    def test_sin_tope_lo_recorre_todo(self):
        libros, a_medias, rondas, motivo = self.recoger(cc.Presupuesto(self.fuente([]), 999, 999))
        self.assertEqual((set(libros), a_medias, motivo), ({self.A, self.B, self.C, self.D}, [], ''))
        self.assertEqual(libros[self.C]['categoria'], 'dos')
        self.assertGreaterEqual(rondas, 2)

    def test_va_por_rondas_la_pagina_1_de_todos_antes_que_la_2(self):
        pedidas = []
        self.recoger(cc.Presupuesto(self.fuente(pedidas), 999, 999))
        listados = [u for u in pedidas if '/categoria/' in u]
        self.assertTrue(all('page=1' in u for u in listados[:2]), listados[:3])

    def test_tope_de_peticiones_deja_informe_parcial(self):
        # 4 peticiones = la primera ronda entera (listado + ficha por categoría); la segunda no empieza.
        presupuesto = cc.Presupuesto(self.fuente([]), 4, 999)
        libros, a_medias, rondas, motivo = self.recoger(presupuesto)
        self.assertEqual(set(libros), {self.A, self.C})
        self.assertEqual((a_medias, rondas, presupuesto.peticiones), (['uno/novedades', 'dos/novedades'], 1, 4))
        self.assertIn('peticiones', motivo)

    def test_tope_de_tiempo(self):
        reloj = iter(range(0, 10000, 10))
        _libros, a_medias, rondas, motivo = self.recoger(
            cc.Presupuesto(self.fuente([]), 999, 25, reloj=lambda: next(reloj)))
        self.assertTrue(a_medias)
        self.assertIn('minutos', motivo)
        self.assertEqual(rondas, 0)  # ni la primera ronda: main lo da por fallo

    def test_fuente_caida_se_corta_pronto(self):
        pedidas = []

        def get(url):
            pedidas.append(url)
            raise OSError('timed out')
        presupuesto = cc.Presupuesto(get, 999, 999, max_errores_seguidos=3)
        libros, a_medias, _rondas, motivo = cc.recoger(
            presupuesto.fetch, [(str(n), 'novedades', 'desc') for n in range(9)], '2026-11-14', '2026-11-16')
        self.assertEqual((libros, len(pedidas)), ({}, 3))
        self.assertEqual(len(a_medias), 6)
        self.assertIn('seguidas', motivo)
        self.assertEqual(len(presupuesto.errores), 3)


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
