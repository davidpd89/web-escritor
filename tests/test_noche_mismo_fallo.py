"""Mismo código, mismo fallo: la noche no se gasta repitiendo una carga que caerá igual (25/11).

La noche del 24 al 25/11 la puerta de la PR de datos cayó en `tests/test-publish-determinista-logs-ansi.py` (main en
rojo) a las 02:50; el reintento y los relojes de las 01:47 y 03:17 relanzaron con el mismo código, cayeron en el mismo
test y la noche murió con MAX_FALLIDOS sin que nada intentara arreglarlo. Aquí se reproduce esa noche con el libro real
(noche.py) y el publicador real (publish-radar-refresh.py), sin red.
"""
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import noche  # noqa: E402

spec = importlib.util.spec_from_file_location('publish_radar_refresh_mf', ROOT / 'scripts/publish-radar-refresh.py')
pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)

UTC = timezone.utc
T0 = datetime(2026, 11, 25, 0, 21, tzinfo=UTC)  # 01:21 en Madrid
FIRMA = 'tests/test-publish-determinista-logs-ansi.py'


def ida_y_vuelta(libro):
    return json.loads(json.dumps(libro))


def carga_fallida(libro, t, run, motivo, codigo, clase=noche.DETERMINISTA, firma=FIRMA):
    cargar, porque, libro = noche.abrir(libro, t, run, 1, 'sha', motivo, codigo)
    assert cargar, porque
    return ida_y_vuelta(noche.cerrar(libro, t + timedelta(minutes=90), run, 1, 'failure', clase=clase, firma=firma,
                                     codigo=codigo))


class LibroTest(unittest.TestCase):
    def test_la_noche_del_25_ya_no_se_repite(self):
        libro = carga_fallida(None, T0, 1, 'cron', 'C1')
        fin = T0 + timedelta(minutes=90)
        toca, porque = noche.toca_reintento(libro, fin, 1, 1)
        self.assertFalse(toca, porque)
        self.assertIn(FIRMA, porque)
        # El reloj de las 01:47 UTC (y cualquier respaldo) con el mismo código no carga.
        for motivo in ('cron', 'respaldo'):
            cargar, porque, _ = noche.abrir(libro, T0 + timedelta(hours=2), 2, 1, 'sha2', motivo, 'C1')
            self.assertFalse(cargar, (motivo, porque))
            self.assertIn('mismo código', porque)
        # Un despacho que llegue igualmente (cadena o reintento con su pendiente) tampoco.
        con_pendiente = noche.pendiente(libro, fin, 'reintento')
        cargar, porque, _ = noche.abrir(con_pendiente, fin + timedelta(minutes=1), 3, 1, 's', 'reintento', 'C1')
        self.assertFalse(cargar, porque)
        # Un commit de datos o de redes no cambia la huella; un arreglo en main sí, y entonces se carga.
        cargar, porque, libro2 = noche.abrir(libro, T0 + timedelta(hours=2), 4, 1, 'sha3', 'cron', 'C2')
        self.assertTrue(cargar, porque)
        self.assertEqual(libro2['intentos'][-1]['codigo'], 'C2')
        # Una carga manual carga siempre.
        self.assertTrue(noche.abrir(libro, T0 + timedelta(hours=2), 5, 1, 's', 'manual', 'C1')[0])

    def test_un_fallo_no_determinista_se_sigue_reintentando(self):
        libro = carga_fallida(None, T0, 1, 'cron', 'C1', clase=None, firma=None)
        self.assertTrue(noche.toca_reintento(libro, T0 + timedelta(minutes=90), 1, 1)[0])
        self.assertTrue(noche.abrir(libro, T0 + timedelta(hours=2), 2, 1, 's', 'cron', 'C1')[0])

    def test_sin_huella_no_se_bloquea(self):
        """git no respondió: sin huella con que comparar se carga como antes (nunca se pierde una noche por esto)."""
        libro = carga_fallida(None, T0, 1, 'cron', None)
        self.assertTrue(noche.abrir(libro, T0 + timedelta(hours=2), 2, 1, 's', 'cron', None)[0])
        libro = carga_fallida(None, T0, 1, 'cron', 'C1')
        self.assertTrue(noche.abrir(libro, T0 + timedelta(hours=2), 2, 1, 's', 'cron', None)[0])

    def test_solo_cuenta_la_ultima_carga(self):
        """Tras el fallo determinista, otra carga con otro código fue bien o falló por otra cosa: ya no bloquea."""
        libro = carga_fallida(None, T0, 1, 'cron', 'C1')
        libro = carga_fallida(libro, T0 + timedelta(hours=2), 2, 'manual', 'C1', clase=None, firma=None)
        self.assertTrue(noche.abrir(libro, T0 + timedelta(hours=4), 3, 1, 's', 'cron', 'C1')[0])

    def test_el_juez_sin_huella_deja_decidir_al_job(self):
        """El juez (job clock) no bloquea: si lo hiciera, la ejecución saldría verde y la autorreparación no la vería."""
        libro = carga_fallida(None, T0, 1, 'cron', 'C1')
        self.assertTrue(noche.decidir(libro, T0 + timedelta(hours=2))[0])


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.guardado = {}

    def lanzar(self, accion, libro, codigo, resultado='failure', motivo='cron'):
        argumentos = SimpleNamespace(motivo=motivo, resultado=resultado)
        salida, errores = io.StringIO(), io.StringIO()
        with mock.patch.object(noche, 'leer', return_value=libro), \
             mock.patch.object(noche, 'escribir', side_effect=lambda n, m: self.guardado.update(libro=n)), \
             mock.patch.object(noche, '_codigo', return_value=codigo), \
             mock.patch.object(noche, '_head', return_value='sha'), \
             mock.patch.dict(os.environ, {'RUNNER_TEMP': self.tmp.name, 'GITHUB_STEP_SUMMARY': ''}), \
             redirect_stdout(salida), redirect_stderr(errores):
            rc = noche.ACCIONES[accion](T0 + timedelta(hours=2), 9, 1, argumentos)
        return rc, salida.getvalue(), errores.getvalue()

    def test_cerrar_anota_la_firma_que_dejo_el_publicador(self):
        pub.anotar_fallo([FIRMA], {'RUNNER_TEMP': self.tmp.name})
        libro = noche.abrir(None, T0, 9, 1, 'sha', 'cron', 'C1')[2]
        self.assertEqual(self.lanzar('cerrar', libro, 'C1')[0], 0)
        entrada = self.guardado['libro']['intentos'][-1]
        self.assertEqual((entrada['resultado'], entrada['clase'], entrada['firma'], entrada['codigo']),
                         ('fallido', noche.DETERMINISTA, FIRMA, 'C1'))

    def test_cerrar_en_verde_no_hereda_una_firma(self):
        pub.anotar_fallo([FIRMA], {'RUNNER_TEMP': self.tmp.name})
        libro = noche.abrir(None, T0, 9, 1, 'sha', 'cron', 'C1')[2]
        self.lanzar('cerrar', libro, 'C1', resultado='success')
        self.assertIsNone(self.guardado['libro']['intentos'][-1]['clase'])

    def test_abrir_bloqueado_sale_en_rojo(self):
        libro = carga_fallida(None, T0, 1, 'cron', 'C1')
        rc, salida, errores = self.lanzar('abrir', libro, 'C1')
        self.assertEqual(rc, 3)
        self.assertIn('cargar=false', salida)
        self.assertIn('::error::', errores)
        rc, salida, _ = self.lanzar('abrir', libro, 'C2')
        self.assertEqual((rc, 'cargar=true' in salida), (0, True))

    def test_abrir_que_no_carga_por_otra_razon_sigue_en_verde(self):
        """Una cadena sin pendiente (ya la cargó otro): no carga y sale en verde; solo el bloqueo por mismo fallo
        pone el job en rojo."""
        libro = carga_fallida(None, T0, 1, 'cron', 'C1', clase=None, firma=None)
        rc, salida, _ = self.lanzar('abrir', libro, 'C1', motivo='cadena')
        self.assertEqual((rc, 'cargar=false' in salida), (0, True))

    def test_huella_real_ignora_commits_de_datos(self):
        """La huella sale del árbol de código de HEAD; en este checkout existe y es estable."""
        a, b = noche._codigo(), noche._codigo()
        self.assertTrue(a)
        self.assertEqual(a, b)


class PublicadorTest(unittest.TestCase):
    def test_firmas_de_los_registros(self):
        log = ('2026-11-25T01:50:01.1Z FALLA: tests/test-b.py\n'
               '2026-11-25T01:50:01.2Z FALLA: tests/test_a.py\n'
               '2026-11-25T01:50:01.3Z FALLA: tests/test-b.py\n')

        def gh(*args):
            if args[0] == 'api' and args[-1].split('?')[0].endswith('/jobs'):
                return json.dumps({'jobs': [{'id': 7, 'conclusion': 'failure'}], 'total_count': 1})
            return log
        with mock.patch.object(pub, 'gh', gh):
            firmas = pub.firmas_deterministas('o/r', 1)
            self.assertTrue(pub.fallo_determinista('o/r', 1))
        self.assertEqual(firmas, ['tests/test-b.py', 'tests/test_a.py'])

    def test_anotar_sin_runner_temp_no_escribe(self):
        pub.anotar_fallo([FIRMA], {})  # local: no revienta ni escribe en ningún sitio

    def test_el_publicador_anota_al_caer_por_un_test(self):
        """La rama que lanza «PR left open» por un test concreto deja antes la firma (lectura del código real)."""
        fuente = (ROOT / 'scripts/publish-radar-refresh.py').read_text(encoding='utf-8')
        bloque = fuente[fuente.index('firmas = firmas_deterministas(repo'):fuente.index("failed ({result[\"databaseId\"]}); PR left open")]
        self.assertIn('anotar_fallo(firmas)', bloque)


class WorkflowTest(unittest.TestCase):
    def test_el_paso_que_abre_falla_el_job_y_nada_carga_despues(self):
        import yaml
        flujo = yaml.safe_load((ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8'))
        pasos = flujo['jobs']['intake']['steps']
        libro = next(p for p in pasos if p.get('id') == 'libro')
        self.assertNotIn('continue-on-error', libro)
        self.assertIn('noche.py abrir', libro['run'])
        cierre = next(p for p in pasos if p.get('name') == 'Close the night turn')
        self.assertIn("steps.libro.outputs.cargar == 'true'", cierre['if'])


if __name__ == '__main__':
    unittest.main()
