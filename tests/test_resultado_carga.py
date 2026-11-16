"""Fable R4-5 (D2 y F2): la carga acaba publicada, degradada o fallida, y el fallo lleva clase y firma.

Antes, un fallo de Amazon o del mercado después de publicar acababa en rojo: el reintento repetía a ciegas y el juez
contaba la noche como perdida. Y la guarda de #1380 («main avanzó») se abría con cualquier commit de un bot.
"""
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
        error, informe = self.correr(AssertionError('test_reading_texts: libro 9788412345678 con un módulo'))
        self.assertIsInstance(error, AssertionError, 'el fallo sigue a la vista')
        self.assertEqual((informe['resultado'], informe['clase']), ('fallido', 'codigo'))
        self.assertEqual(len(informe['firma']), 12)

    def test_main_movido_es_transitorio(self):
        error, informe = self.correr(refresh.publisher.publication.StaleMerge('main se movió'))
        self.assertEqual(error.code, refresh.publisher.publication.STALE_EXIT_CODE)
        self.assertEqual((informe['resultado'], informe['clase']), ('fallido', 'transitorio'))


class ClaseYFirmaTest(unittest.TestCase):
    def test_clases(self):
        def envuelto(causa):
            try:
                raise RuntimeError('La PR de la carga no llegó a verde') from causa
            except RuntimeError as exc:
                return exc
        casos = {
            'transitorio': [urllib.error.HTTPError('u', 502, 'Bad Gateway', {}, None), urllib.error.URLError('x'),
                            TimeoutError('Creators API'), envuelto(ConnectionResetError()),
                            subprocess.CalledProcessError(1, ['gh'], stderr='HTTP 502: Bad Gateway'),
                            RuntimeError('API rate limit exceeded')],
            'codigo': [AssertionError('2 != 1'), KeyError('isbn'), urllib.error.HTTPError('u', 404, 'NF', {}, None),
                       envuelto(ValueError('ISBN repetido')),
                       subprocess.CalledProcessError(1, ['python', 'tests/x.py'], stderr='FAILED (failures=1)')],
        }
        for esperada, excepciones in casos.items():
            for exc in excepciones:
                with self.subTest(exc=repr(exc)):
                    self.assertEqual(rc.clase(exc), esperada)

    def test_la_firma_no_cambia_con_el_lote_y_si_con_el_fallo(self):
        a = rc.firma(AssertionError('libro 9788412345678 en la ejecución 43816841127 (commit 9bd9aa3cc0)'))
        b = rc.firma(AssertionError('libro 9791388351112 en la ejecución 43832706031 (commit 276e091808)'))
        c = rc.firma(AssertionError('portada duplicada en 9788412345678'))
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, rc.firma(KeyError('libro 9788412345678 en la ejecución 1 (commit 9bd9aa3cc0)')))


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

    def test_degradado_no_es_fallido(self):
        toca, porque = self.decide(intento(1, 'degradado', None, 'ddd'))
        self.assertFalse(toca)
        self.assertIn('degradado', porque)
        self.assertFalse(noche.decidir({'dia': '2026-11-16', 'intentos': [intento(1, 'degradado')]}, AHORA)[0],
                         'un reloj no repite una carga degradada: ya publicó')


class CierreTest(unittest.TestCase):
    def test_el_cierre_toma_resultado_clase_y_firma_de_la_carga(self):
        deg = {'resultado': 'degradado', 'degradado': [{'paso': 'mercado', 'firma': 'f1'}]}
        self.assertEqual(noche.resultado_de_la_carga('success', deg), ('degradado', None, 'f1'))
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
        self.assertEqual(wf['permissions'].get('issues'), 'write')
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
