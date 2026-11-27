"""Propiedades de la carga nocturna con Hypothesis (ronda 4 de la revisión GPT, 25/11).

Tras cuatro rondas de casos sueltos, el riesgo que queda es que dos mecanismos correctos por separado rompan juntos
(lo que hicieron #1564 y #1395). Aquí no se prueba un caso: se prueban cientos de secuencias y entradas y se exige
que se conserven los invariantes.

- El libro de la noche (noche.py) como máquina de estados: aperturas por cualquier motivo, cierres, runners que
  mueren sin cerrar, huérfanas, despachos de cadena y reintento, el reloj que cruza la medianoche.
- priorizar() y seed_batches(): ningún candidato ni ISBN se pierde ni se duplica, con fechas cualesquiera.
- altas_max(): nunca más altas que el tope ni que el hueco, y un sitio más grande nunca recibe más.

`derandomize=True`: la puerta repite un contrato que falla para separar lo determinista de lo inestable
(confirmar_fallos.py); con ejemplos aleatorios cada vuelta probaría otra cosa. Siempre los mismos ejemplos, y un
fallo se reproduce igual en local.
"""
import json
import sys
import unittest
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import catalogo_amazon as ca  # noqa: E402
import noche  # noqa: E402
import presupuesto_sitio as ps  # noqa: E402

FIJO = settings(derandomize=True, deadline=None, suppress_health_check=[HealthCheck.too_slow])
CERRADOS = ('publicado', 'degradado', 'fallido', 'cancelado')
MOTIVOS = ('cron', 'respaldo', 'manual', 'cadena', 'reintento')


class LibroDeLaNoche(RuleBasedStateMachine):
    """Una noche cualquiera contra noche.py, con el libro guardado en JSON entre paso y paso como en catalogo-estado.

    El grupo de concurrencia de `intake` deja una sola carga viva: solo se abre si no hay ninguna viva (la muerta
    no cuenta, como un runner perdido)."""

    def __init__(self):
        super().__init__()
        self.libro = None
        self.now = datetime(2026, 11, 25, 0, 17, tzinfo=timezone.utc)
        self.run = 100
        self.viva = None          # (run, intento) de la carga que corre
        self.muertas = []         # runners perdidos sin cerrar su apunte
        self.cerradas = {}        # (dia, run, intento) → resultado con que se cerró

    def guardar(self, libro):
        self.libro = json.loads(json.dumps(libro))   # lo que sobrevive a la rama: solo JSON

    @rule(minutos=st.integers(0, 240))
    def pasa_el_tiempo(self, minutos):
        self.now += timedelta(minutes=minutos)

    @precondition(lambda self: self.viva is None)
    @rule(motivo=st.sampled_from(MOTIVOS), codigo=st.sampled_from(('A', 'B', None)))
    def abrir(self, motivo, codigo):
        self.run += 1
        antes = noche.resumen(self.libro, self.now)
        cargar, porque, libro = noche.abrir(self.libro, self.now, self.run, 1, 'sha', motivo, codigo)
        assert isinstance(porque, str) and porque
        if motivo != 'manual' and noche.repetiria(antes['ultimo'], codigo) and antes['ultimo'][1] == 'fallido':
            assert not cargar, f'{motivo} repite con el mismo código un fallo determinista: {porque}'
        if motivo == 'manual':
            assert cargar, 'una carga manual carga siempre'
        if motivo in noche.DESPACHADOS and not antes['pendientes']:
            assert not cargar, f'{motivo} sin pendiente cargó: lo cargó otro antes'
        if cargar:
            assert not noche.resumen(libro, self.now)['pendientes'], 'quien carga consume los despachos pendientes'
            self.viva = (self.run, 1)
        self.guardar(libro)

    @precondition(lambda self: self.viva is not None)
    @rule(resultado=st.sampled_from(('success', 'failure', 'cancelled', 'skipped')),
          determinista=st.booleans(), codigo=st.sampled_from(('A', 'B', None)))
    def cerrar(self, resultado, determinista, codigo):
        run, intento = self.viva
        clase = noche.DETERMINISTA if determinista and resultado == 'failure' else None
        libro = noche.cerrar(self.libro, self.now, run, intento, resultado, clase, 'tests/test-x.py', None, codigo)
        otra = noche.cerrar(json.loads(json.dumps(libro)), self.now + timedelta(minutes=5), run, intento, resultado,
                            clase, 'tests/test-x.py', None, codigo)
        assert otra == libro, 'cerrar dos veces (el paso repetido) no cambia el libro'
        self.guardar(libro)
        entrada = self.entrada(run, intento)
        if resultado == 'skipped':
            assert entrada is None, 'una carga omitida no deja apunte'
        else:
            assert entrada is not None and entrada['resultado'] == noche.RESULTADOS[resultado]
            self.cerradas[(self.libro['dia'], run, intento)] = entrada['resultado']
            if resultado == 'failure':
                ok, _ = noche.toca_reintento(self.libro, self.now, run, intento)
                if ok:
                    assert not determinista, 'un fallo determinista no se reintenta con el mismo código'
                    self.guardar(noche.pendiente(self.libro, self.now, 'reintento'))
            if resultado == 'success' and noche.toca_cadena(self.libro, self.now, 1)[0]:
                self.guardar(noche.pendiente(self.libro, self.now, 'cadena'))
        self.viva = None

    @precondition(lambda self: self.viva is not None)
    @rule()
    def muere_el_runner(self):
        self.muertas.append(self.viva)
        self.viva = None

    @precondition(lambda self: self.muertas)
    @rule(cual=st.integers(0, 10))
    def segador_de_huerfanas(self, cual):
        run, intento = self.muertas[cual % len(self.muertas)]
        antes = {(i.get('run'), i.get('intento')): dict(i) for i in (self.libro or {}).get('intentos', [])}
        libro, cerrada = noche.huerfana(self.libro, self.now, run, intento)
        self.guardar(libro)
        for i in (self.libro or {}).get('intentos', []):
            clave = (i.get('run'), i.get('intento'))
            if clave != (run, intento) and clave in antes:
                assert i == antes[clave], 'la huérfana solo toca su propio apunte'
        if cerrada:
            assert self.entrada(run, intento)['clase'] == 'corte'

    @rule()
    def juez(self):
        cargar, porque = noche.decidir(self.libro, self.now)
        r = noche.resumen(self.libro, self.now)
        if r['fallidos'] >= noche.MAX_FALLIDOS:
            assert not cargar, porque

    def entrada(self, run, intento):
        return next((i for i in (self.libro or {}).get('intentos', [])
                     if (i.get('run'), i.get('intento')) == (run, intento)), None)

    @invariant()
    def una_sola_en_curso(self):
        en_curso = [i for i in (self.libro or {}).get('intentos', []) if i.get('resultado') == 'en_curso']
        assert len(en_curso) <= 1, en_curso

    @invariant()
    def sin_apuntes_repetidos(self):
        claves = [(i.get('run'), i.get('intento')) for i in (self.libro or {}).get('intentos', [])
                  if i.get('resultado') != 'pendiente']
        assert len(claves) == len(set(claves)), claves

    @invariant()
    def lo_cerrado_tiene_fin_y_no_se_reabre(self):
        libro = self.libro or {}
        for i in libro.get('intentos', []):
            if i.get('resultado') in CERRADOS:
                assert i.get('fin'), i
            previo = self.cerradas.get((libro.get('dia'), i.get('run'), i.get('intento')))
            if previo:
                assert i.get('resultado') == previo, f'un apunte cerrado {previo} pasó a {i.get("resultado")}'


TestLibroDeLaNoche = LibroDeLaNoche.TestCase
TestLibroDeLaNoche.settings = settings(FIJO, max_examples=300, stateful_step_count=40)


FECHAS = st.one_of(
    st.dates(min_value=datetime(2024, 1, 1).date(), max_value=datetime(2028, 12, 31).date()).map(lambda d: d.isoformat()),
    st.sampled_from(('', '2026-11-31', '2027-02-29', '2026-13-01', '2026-11', '2026-11-25T00:00:00Z', 'mañana')))


def registro(n, fecha, materia, rango):
    item = {'asin': f'B{n:09d}'}
    if rango is not None:
        item['browseNodeInfo'] = {'websiteSalesRank': {'salesRank': rango}}
    return {'asin': f'B{n:09d}', 'item': item, 'fecha_publicacion_edicion': fecha, 'materias': [materia]}


class Priorizar(unittest.TestCase):
    @FIJO
    @given(filas=st.lists(st.tuples(FECHAS, st.sampled_from(('novela', 'ensayo', '')),
                                    st.one_of(st.none(), st.integers(-5, 10**6), st.just('123'))), max_size=60),
           limite=st.integers(0, 70), esperando=st.lists(st.integers(0, 59), max_size=20),
           dia=st.sampled_from(('2026-11-25', '2026-12-31', '2028-02-29')))
    def test_ningun_candidato_se_pierde_ni_se_duplica(self, filas, limite, esperando, dia):
        candidatos = [registro(n, *fila) for n, fila in enumerate(filas)]
        waiting = {f'B{n:09d}': '2026-11-01' for n in esperando if n < len(candidatos)}
        elegidos, aplazados = ca.priorizar(candidatos, dia, limite, waiting)
        self.assertEqual(len(elegidos), min(limite, len(candidatos)))
        self.assertEqual(Counter(map(id, elegidos + aplazados)), Counter(map(id, candidatos)))


def isbn13(prefijo, n):
    cuerpo = f'{prefijo}{n:0{12 - len(prefijo)}d}'
    suma = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(cuerpo))
    return cuerpo + str((-suma) % 10)


class LotesDeSemillas(unittest.TestCase):
    @FIJO
    @given(filas=st.lists(st.tuples(st.sampled_from(('97884', '97913')), st.integers(0, 9_999_999),
                                    st.integers(0, 6)), max_size=150, unique_by=lambda f: (f[0], f[1])))
    def test_cada_isbn_va_en_un_solo_lote_de_su_via(self, filas):
        cola = {isbn13(p, n): {'errores': e} for p, n, e in filas}
        lotes = list(ca.seed_batches(list(cola), cola))
        vistos = [i for _, lote in lotes for i in lote]
        self.assertEqual(Counter(vistos), Counter(list(cola)))
        for via, lote in lotes:
            self.assertTrue(1 <= len(lote) <= 10)
            self.assertTrue(all(ca.seed_kind(i) == via for i in lote))
            if len(lote) > 1:
                self.assertTrue(all(cola[i]['errores'] < ca.SPLIT_AFTER for i in lote), 'un ISBN que falla va suelto')


class PresupuestoDelSitio(unittest.TestCase):
    @FIJO
    @given(usados=st.integers(0, 1000 * ps.MB), crece=st.integers(0, 100 * ps.MB), coste=st.integers(1, ps.MB),
           medidos=st.integers(1, 20000), nuevos=st.integers(0, 400), hechas=st.integers(0, 300),
           tope=st.one_of(st.none(), st.integers(1, 2000)))
    def test_nunca_pasa_del_tope_ni_del_freno(self, usados, crece, coste, medidos, nuevos, hechas, tope):
        medida = {'bytes': usados, 'libros': medidos, 'coste_por_libro': coste}
        cupo = ps.altas_max(medida, medidos + nuevos, hechas, tope)
        self.assertGreaterEqual(cupo, 0)
        if tope is not None:
            self.assertLessEqual(cupo, max(0, tope - hechas))
        self.assertLessEqual(usados + (nuevos + cupo) * coste, max(usados + nuevos * coste, ps.FRENO_MB * ps.MB))
        mayor = ps.altas_max(dict(medida, bytes=usados + crece), medidos + nuevos, hechas, tope)
        self.assertLessEqual(mayor, cupo, 'un sitio más grande no recibe más altas')
        self.assertLessEqual(ps.altas_max(medida, medidos + nuevos + 1, hechas, tope), cupo, 'ni con más libros publicados')


if __name__ == '__main__':
    unittest.main()
