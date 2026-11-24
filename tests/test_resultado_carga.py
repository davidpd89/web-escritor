"""Fable R4-5 (D2 y F2): la carga acaba publicada, degradada o fallida, y el fallo lleva clase y firma.

Antes, un fallo de Amazon o del mercado después de publicar acababa en rojo: el reintento repetía a ciegas y el juez
contaba la noche como perdida. Y la guarda de #1380 («main avanzó») se abría con cualquier commit de un bot.
"""
import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import noche  # noqa: E402
import resultado_carga as rc  # noqa: E402

spec = importlib.util.spec_from_file_location('refresh_tres_estados', ROOT / 'scripts/refresh-reading-catalogue.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)

AHORA = datetime(2026, 11, 16, 2, 30, tzinfo=timezone.utc)  # 03:30 de Madrid


class F2Test(unittest.TestCase):
    """Excepción inyectada en el mercado ⇒ código 0, informe `degradado: [mercado]` (y la cadena sigue)."""

    def correr(self, efecto):
        with tempfile.TemporaryDirectory() as tmp, patch.object(refresh, 'ROOT', Path(tmp)), \
                patch.object(refresh, 'refresh', side_effect=efecto):
            error = None
            try:
                refresh.main(True)
            except BaseException as exc:  # noqa: BLE001
                error = exc
            return error, rc.leer(Path(tmp))

    def test_mercado_que_falla_tras_publicar_sale_en_verde_y_degradado(self):
        def carga(publish):
            refresh.DESCARTADOS['mercado'] = TimeoutError('Creators API')
        error, informe = self.correr(carga)
        self.assertIsNone(error, 'una carga que publicó no acaba en rojo')
        self.assertEqual(informe['resultado'], 'degradado')
        self.assertEqual([p['paso'] for p in informe['degradado']], ['mercado'])
        self.assertEqual(rc.a_reportar(informe)[0]['paso'], 'mercado', 'va a una issue `fallo`')

    def test_sin_descartes_es_publicado(self):
        error, informe = self.correr(lambda publish: refresh.DESCARTADOS.clear())
        self.assertIsNone(error)
        self.assertEqual(informe['resultado'], 'publicado')
        self.assertEqual(rc.a_reportar(informe), [])

    def test_fallo_antes_de_publicar_es_fallido_con_clase_y_firma(self):
        def carga(publish):
            with rc.etapa('construccion'):
                raise AssertionError('test_reading_texts: libro 9788412345678 con un módulo')
        error, informe = self.correr(carga)
        self.assertIsInstance(error, AssertionError, 'el fallo sigue a la vista (mismo tipo, con su etapa)')
        self.assertEqual((informe['resultado'], informe['clase']), ('fallido', 'codigo'))
        self.assertEqual(len(informe['firma']), 12)

    def test_fallo_fuera_de_toda_etapa_es_desconocido_y_se_reporta(self):
        error, informe = self.correr(AssertionError('sin etapa'))
        self.assertIsInstance(error, AssertionError)
        self.assertEqual((informe['resultado'], informe['clase']), ('fallido', 'desconocido'))
        self.assertTrue(rc.a_reportar(informe), 'un desconocido abre issue para mirarlo de día')

    def test_main_movido_es_transitorio(self):
        error, informe = self.correr(refresh.publisher.publication.StaleMerge('main se movió'))
        self.assertEqual(error.code, refresh.publisher.publication.STALE_EXIT_CODE)
        self.assertEqual((informe['resultado'], informe['clase']), ('fallido', 'transitorio'))


def en(nombre, exc, regla=None):
    """La excepción tal como sale de un bloque `with rc.etapa(nombre)`."""
    try:
        with rc.etapa(nombre, regla):
            raise exc
    except BaseException as fuera:  # noqa: BLE001
        return fuera


def envuelto(causa, nombre=None):
    try:
        try:
            raise RuntimeError('La PR de la carga no llegó a verde') from causa
        except RuntimeError as exc:
            raise exc
    except RuntimeError as exc:
        return en(nombre, exc) if nombre else exc


class ClaseYFirmaTest(unittest.TestCase):
    """R5-12: la clase sale de la etapa (o del tipo, para red y HTTP), nunca del texto del mensaje."""

    def test_clase_por_etapa(self):
        for nombre, esperada in rc.CLASE_DE_ETAPA.items():
            with self.subTest(etapa=nombre):
                self.assertEqual(rc.clase(en(nombre, AssertionError('x'))), esperada)
        self.assertEqual(rc.clase(AssertionError('x')), 'desconocido', 'sin etapa no se da por código')
        self.assertEqual(rc.clase(envuelto(ValueError('ISBN repetido'), 'consulta')), 'transitorio',
                         'la etapa de un eslabón exterior cuenta para toda la cadena')
        with self.assertRaises(ValueError):
            with rc.etapa('inventada'):
                pass

    def test_clase_por_tipo_manda_sobre_la_etapa(self):
        casos = {
            'transitorio': [en('construccion', urllib.error.HTTPError('u', 502, 'Bad Gateway', {}, None)),
                            urllib.error.URLError('x'), TimeoutError('Creators API'),
                            envuelto(ConnectionResetError(), 'publicacion'),
                            en('contrato', urllib.error.HTTPError('u', 429, 'Too Many', {}, None))],
            'codigo': [en('consulta', urllib.error.HTTPError('u', 404, 'NF', {}, None))],
        }
        for esperada, excepciones in casos.items():
            for exc in excepciones:
                with self.subTest(exc=repr(exc)):
                    self.assertEqual(rc.clase(exc), esperada)

    def test_el_texto_no_cambia_ni_la_clase_ni_la_firma(self):
        # Antes 'API rate limit exceeded' o un stderr con «HTTP 502» se daban por transitorios por su texto.
        for texto in ('API rate limit exceeded', 'HTTP 502: Bad Gateway', 'SSL TLS timed out', '2 != 1'):
            with self.subTest(texto=texto):
                exc = en('construccion', RuntimeError(texto))
                self.assertEqual(rc.clase(exc), 'codigo')
                self.assertEqual(rc.firma(exc), rc.firma(en('construccion', RuntimeError('otro texto'))))
        a = en('construccion', subprocess.CalledProcessError(1, ['python', 'scripts/build-reading-catalogue.py', '--x', '9788412345678'],
                                                             stderr='HTTP 502'))
        b = en('construccion', subprocess.CalledProcessError(2, ['python', 'scripts/build-reading-catalogue.py'], stderr='otro'))
        c = en('construccion', subprocess.CalledProcessError(1, ['python', 'scripts/build-reading-pinterest-rss.py']))
        self.assertEqual(rc.firma(a), rc.firma(b), 'la firma de un subproceso es su programa, no la orden entera')
        self.assertNotEqual(rc.firma(a), rc.firma(c))

    def test_etapa_regla_y_tipo_si_cambian_la_firma(self):
        base = rc.firma(en('contrato', RuntimeError('x'), 'test_a'))
        self.assertEqual(base, rc.firma(en('contrato', RuntimeError('libro 9791388351112, ejecución 43832706031'), 'test_a')))
        self.assertNotEqual(base, rc.firma(en('contrato', RuntimeError('x'), 'test_b')))
        self.assertNotEqual(base, rc.firma(en('construccion', RuntimeError('x'))))
        self.assertNotEqual(base, rc.firma(en('contrato', KeyError('x'), 'test_a')))
        self.assertNotEqual(rc.firma(urllib.error.HTTPError('u', 502, 'B', {}, None)),
                            rc.firma(urllib.error.HTTPError('u', 503, 'B', {}, None)))

    def test_la_etapa_no_cambia_el_tipo_y_manda_la_interior(self):
        exc = en('remoto', en('publicacion', refresh.publisher.publication.StaleMerge('main se movió')))
        self.assertIsInstance(exc, refresh.publisher.publication.StaleMerge, 'main la sigue capturando por tipo')
        self.assertEqual(exc.etapa, 'publicacion')

    def test_resultado_carga_no_lee_texto(self):
        arbol = ast.parse((ROOT / 'scripts/resultado_carga.py').read_text(encoding='utf-8'))
        modulos = {a.name for n in ast.walk(arbol) if isinstance(n, ast.Import) for a in n.names}
        modulos |= {n.module for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom)}
        self.assertNotIn('re', modulos, 'la clase y la firma no salen de expresiones sobre el mensaje')
        clasifican = [f for f in arbol.body if isinstance(f, ast.FunctionDef)
                      and f.name in ('clase', 'firma', '_etapa', '_identidad', 'cadena')]
        self.assertEqual(len(clasifican), 5)
        self.assertFalse([(f.name, n.attr) for f in clasifican for n in ast.walk(f) if isinstance(n, ast.Attribute)
                          and n.attr in ('stderr', 'stdout', 'output', 'args', 'reason', 'msg')],
                         'ni del texto de la excepción (el texto solo va al campo `error`, para leerlo)')


class CaminoRealTest(unittest.TestCase):
    """La etapa la pone el código de la carga, no el test: cuarentena que falla dentro de assemble ⇒ entorno."""

    def test_cuarentena_que_falla_en_assemble_es_entorno(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(refresh, 'ROOT', Path(tmp)), \
                patch.object(refresh.reading_quarantine, 'apply', side_effect=KeyError('version publicada')):
            with self.assertRaises(KeyError) as fallo:
                refresh.assemble({'new_books': [], 'updated_books': [], 'stats': {}}, changed=False)
            informe = rc.fallido(fallo.exception)
        self.assertEqual((informe['resultado'], informe['clase']), ('fallido', 'entorno'))
        self.assertFalse(rc.a_reportar(informe), 'entorno no abre issue: lo cubren el reintento y el tope')

    def test_cada_clase_se_reintenta_o_se_reporta(self):
        for c in rc.CLASES:
            with self.subTest(clase=c):
                self.assertTrue(c in rc.SE_REINTENTA or c in rc.SE_REPORTA)
        self.assertEqual(set(rc.SE_REINTENTA) & set(noche.SIN_REINTENTO), set())
        self.assertEqual(set(rc.CLASES) - set(rc.SE_REINTENTA), set(noche.SIN_REINTENTO))


def intento(run, resultado, clase=None, firma=None, sha='c0de', minutos=0):
    return {'run': run, 'intento': 1, 'sha': sha, 'motivo': 'cron', 'inicio': f'2026-11-16T01:{minutos:02d}:00Z',
            'fin': f'2026-11-16T02:{minutos:02d}:00Z', 'resultado': resultado, 'clase': clase, 'firma': firma}


class GuardaPorFirmaTest(unittest.TestCase):
    """La guarda de #1380 con un libro de la noche de ejemplo: no «main avanzó», sino «misma firma, mismo código»."""

    def decide(self, *intentos):
        libro = {'dia': '2026-11-16', 'intentos': list(intentos)}
        return noche.toca_reintento(json.loads(json.dumps(libro)), AHORA, intentos[-1]['run'], 1)

    def test_primer_transitorio_se_reintenta(self):
        self.assertTrue(self.decide(intento(1, 'fallido', 'transitorio', 'aaa'))[0])

    def test_misma_firma_mismo_codigo_no_se_repite(self):
        toca, porque = self.decide(intento(1, 'fallido', 'transitorio', 'aaa'),
                                   intento(2, 'fallido', 'transitorio', 'aaa', minutos=30))
        self.assertFalse(toca)
        self.assertIn('aaa', porque)

    def test_un_commit_de_bot_no_reabre_el_reintento_pero_un_codigo_nuevo_si(self):
        # El commit de seguidores mueve main, pero el código de la carga (sha del intento) es el mismo.
        self.assertFalse(self.decide(intento(1, 'fallido', 'transitorio', 'aaa'),
                                     intento(2, 'fallido', 'transitorio', 'aaa', minutos=30))[0])
        self.assertTrue(self.decide(intento(1, 'fallido', 'transitorio', 'aaa'),
                                    intento(2, 'fallido', 'transitorio', 'aaa', sha='arreglo', minutos=30))[0])

    def test_otra_firma_si_se_reintenta(self):
        self.assertTrue(self.decide(intento(1, 'fallido', 'transitorio', 'aaa'),
                                    intento(2, 'fallido', 'transitorio', 'bbb', minutos=30))[0])

    def test_fallo_de_codigo_nunca_se_reintenta_de_noche(self):
        toca, porque = self.decide(intento(1, 'fallido', 'codigo', 'ccc'))
        self.assertFalse(toca)
        self.assertIn('código', porque)

    def test_fallo_de_dato_no_se_reintenta_y_entorno_o_desconocido_si(self):
        toca, porque = self.decide(intento(1, 'fallido', 'dato', 'eee'))
        self.assertFalse(toca)
        self.assertIn('dato', porque)
        for c in ('entorno', 'desconocido'):
            with self.subTest(clase=c):
                self.assertTrue(self.decide(intento(1, 'fallido', c, 'fff'))[0])
                self.assertFalse(self.decide(intento(1, 'fallido', c, 'fff'), intento(2, 'fallido', c, 'fff', minutos=30))[0],
                                 'misma firma sobre el mismo código: no se repite')

    def test_degradado_no_es_fallido(self):
        toca, porque = self.decide(intento(1, 'degradado', None, 'ddd'))
        self.assertFalse(toca)
        self.assertIn('degradado', porque)
        self.assertFalse(noche.decidir({'dia': '2026-11-16', 'intentos': [intento(1, 'degradado')]}, AHORA)[0],
                         'un reloj no repite una carga degradada: ya publicó')


class CierreTest(unittest.TestCase):
    def test_el_cierre_toma_resultado_clase_y_firma_de_la_carga(self):
        deg = {'resultado': 'degradado', 'degradado': [{'paso': 'mercado', 'firma': 'f1'}]}
        self.assertEqual(noche.resultado_de_la_carga('success', deg), ('degradado', None, ['f1']))
        fal = {'resultado': 'fallido', 'clase': 'codigo', 'firma': 'f2'}
        self.assertEqual(noche.resultado_de_la_carga('failure', fal), ('failure', 'codigo', 'f2'))
        # Sin informe (murió antes de escribirlo) o informe de otro estado: manda el job.
        self.assertEqual(noche.resultado_de_la_carga('failure', None), ('failure', None, None))
        self.assertEqual(noche.resultado_de_la_carga('cancelled', fal), ('cancelled', None, None))
        libro = noche.cerrar({'dia': '2026-11-16', 'intentos': [dict(intento(7, 'en_curso'), fin=None)]}, AHORA, 7, 1,
                             'failure', 'codigo', 'f2')
        self.assertEqual({k: libro['intentos'][0][k] for k in ('resultado', 'clase', 'firma')},
                         {'resultado': 'fallido', 'clase': 'codigo', 'firma': 'f2'})


class IssueTest(unittest.TestCase):
    def gh_falso(self, abiertas):
        llamadas = []

        def gh(args):
            llamadas.append(args)
            return json.dumps(abiertas) if args[:2] == ['issue', 'list'] else ''
        return gh, llamadas

    def test_una_issue_por_firma(self):
        informe = {'resultado': 'fallido', 'clase': 'codigo', 'firma': 'abc123abc123', 'error': 'AssertionError: x'}
        gh, llamadas = self.gh_falso([])
        self.assertEqual(rc.reportar(informe, gh, 'https://run'), ['abierta abc123abc123'])
        crear = llamadas[-1]
        self.assertEqual(crear[:4], ['issue', 'create', '--label', 'fallo'])
        self.assertIn('[firma abc123abc123]', crear[crear.index('--title') + 1])
        gh, llamadas = self.gh_falso([{'number': 9, 'title': rc.titulo({'paso': 'carga', 'firma': 'abc123abc123'})}])
        self.assertEqual(rc.reportar(informe, gh, 'https://run'), ['comentada #9'])
        self.assertEqual(llamadas[-1][:3], ['issue', 'comment', '9'])

    def test_transitorio_y_publicado_no_abren_issue(self):
        gh, llamadas = self.gh_falso([])
        rc.reportar({'resultado': 'fallido', 'clase': 'transitorio', 'firma': 'x'}, gh, '')
        rc.reportar({'resultado': 'publicado', 'degradado': []}, gh, '')
        rc.reportar(None, gh, '')
        self.assertEqual(llamadas, [])


class WorkflowTest(unittest.TestCase):
    def test_issue_tras_cerrar_el_turno_y_antes_de_la_cadena(self):
        wf = yaml.safe_load((ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8'))
        self.assertEqual(wf['jobs']['intake']['permissions'].get('issues'), 'write')
        pasos = wf['jobs']['intake']['steps']
        nombres = [p.get('name', '') for p in pasos]
        issue = nombres.index('Report the failure as a `fallo` issue')
        self.assertLess(nombres.index('Close the night turn'), issue)
        self.assertLess(issue, nombres.index('Chain the next night batch'))
        self.assertIn('always()', pasos[issue]['if'])
        self.assertTrue(pasos[issue].get('continue-on-error'), 'una issue que no se abre no tumba la carga')
        self.assertIn('resultado_carga.py issue', pasos[issue]['run'])


if __name__ == '__main__':
    unittest.main()


class CadenaPorFirmaTest(unittest.TestCase):
    """Hallazgo 6: una carga degradada encadena, pero no si la misma firma ya se degradó esta noche sobre el mismo código."""

    def decide(self, *intentos):
        libro = {'dia': '2026-11-16', 'intentos': list(intentos)}
        return noche.toca_cadena(json.loads(json.dumps(libro)), AHORA, 5, run=intentos[-1]['run'], intento=1)

    def test_primera_degradada_encadena(self):
        self.assertTrue(self.decide(intento(1, 'degradado', None, ['aaa']))[0])

    def test_misma_firma_degradada_no_encadena(self):
        toca, porque = self.decide(intento(1, 'degradado', None, ['aaa', 'bbb']),
                                   intento(2, 'degradado', None, ['bbb'], minutos=30))
        self.assertFalse(toca)
        self.assertIn('bbb', porque)

    def test_otra_firma_u_otro_codigo_si_encadena(self):
        self.assertTrue(self.decide(intento(1, 'degradado', None, ['aaa']),
                                    intento(2, 'degradado', None, ['bbb'], minutos=30))[0])
        self.assertTrue(self.decide(intento(1, 'degradado', None, ['aaa']),
                                    intento(2, 'degradado', None, ['aaa'], sha='arreglo', minutos=30))[0])

    def test_publicada_encadena_aunque_antes_hubiera_degradadas(self):
        self.assertTrue(self.decide(intento(1, 'degradado', None, ['aaa']), intento(2, 'success', minutos=30))[0])
