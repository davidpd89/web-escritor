"""Registro de empleados: cada workflow tiene departamento y el latido juzga bien quién ficha. Sin red."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import empleados_latido as e  # noqa: E402

AHORA = datetime(2026, 11, 16, 7, 0, tzinfo=timezone.utc)


def runs(*conclusiones, cada_horas=24):
    return [{'conclusion': c, 'url': 'u%d' % i, 'fecha': AHORA - timedelta(hours=1 + cada_horas * i)}
            for i, c in enumerate(conclusiones)]


class RegistroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registro, cls.workflows = e.cargar_registro(), e.workflows_del_repo()

    def test_registro_y_repositorio_cuadran(self):
        self.assertEqual(e.fallos_registro(self.registro, self.workflows), [])

    def test_cada_workflow_esta_en_un_solo_departamento(self):
        vistos = [w for dep in self.registro['departamentos'] for w in dep.get('workflows', [])]
        self.assertEqual(sorted(vistos), sorted(set(vistos)))

    def test_un_workflow_nuevo_sin_departamento_se_detecta(self):
        nuevos = dict(self.workflows, **{'recien-llegado': {'fichero': 'recien-llegado.yml', 'eventos': set(), 'crons': []}})
        self.assertTrue(any('recien-llegado' in f for f in e.fallos_registro(self.registro, nuevos)))

    def test_un_workflow_borrado_se_detecta(self):
        menos = {k: v for k, v in self.workflows.items() if k != 'codeql'}
        self.assertTrue(any('codeql' in f for f in e.fallos_registro(self.registro, menos)))

    def test_un_departamento_vacio_necesita_decir_por_que(self):
        registro = {'departamentos': [{'id': 'x', 'nombre': 'X', 'mision': 'm', 'workflows': []}]}
        self.assertTrue(any('vacante' in f for f in e.fallos_registro(registro, {})))

    def test_lo_evaluado_necesita_herramienta_y_motivo(self):
        for clave in ('descartados', 'pendientes', 'cubiertos'):
            registro = {'departamentos': [{'id': 'x', 'nombre': 'X', 'mision': 'm', 'vacante': 'v', clave: [{'herramienta': 'Y'}]}]}
            self.assertTrue(any('sin motivo' in f for f in e.fallos_registro(registro, {})), clave)

    def test_ninguna_herramienta_se_evalua_dos_veces(self):
        vistas = [item['herramienta'] for dep in self.registro['departamentos']
                  for clave in ('descartados', 'pendientes', 'cubiertos') for item in dep.get(clave, [])]
        self.assertEqual(sorted(vistas), sorted(set(vistas)))

    def test_se_leen_los_horarios_de_los_ficheros(self):
        self.assertEqual(self.workflows['production-smoke-monitor']['crons'], ['17 */6 * * *'])
        self.assertIn('schedule', self.workflows['empleados-latido']['eventos'])
        self.assertEqual(self.workflows['autor-browser-qa']['crons'], [])


class PlazoTests(unittest.TestCase):
    def test_plazo_segun_el_horario(self):
        self.assertIsNone(e.plazo_dias([]))
        self.assertEqual(e.plazo_dias(['17 */6 * * *']), 2)
        self.assertEqual(e.plazo_dias(['23 5 * * 1']), 9)
        self.assertEqual(e.plazo_dias(['0 4 1 * *']), 35)
        self.assertEqual(e.plazo_dias(['0 4 1 * *', '5 5 * * *']), 2)


class JuzgarTests(unittest.TestCase):
    def estado(self, ejecuciones, plazo=2):
        return e.juzgar(ejecuciones, plazo, AHORA)[0]

    def test_verde(self):
        self.assertEqual(self.estado(runs('success', 'failure', 'failure', 'failure')), 'ok')

    def test_una_roja_es_inestable_y_tres_seguidas_es_rojo(self):
        self.assertEqual(self.estado(runs('failure', 'success')), 'inestable')
        self.assertEqual(self.estado(runs('failure', 'timed_out', 'success')), 'inestable')
        self.assertEqual(self.estado(runs('failure', 'failure', 'timed_out', 'success')), 'rojo')

    def test_nunca_ha_salido_verde(self):
        self.assertEqual(self.estado(runs('failure', 'failure')), 'rojo')

    def test_las_canceladas_no_cuentan(self):
        self.assertEqual(self.estado(runs('cancelled', 'success')), 'ok')
        self.assertEqual(self.estado(runs('failure', 'cancelled', 'skipped', 'failure', 'failure', 'success')), 'rojo')

    def test_con_horario_y_sin_fichar_es_ausente(self):
        self.assertEqual(self.estado([]), 'ausente')
        self.assertEqual(self.estado(runs('success', cada_horas=24)[:1], plazo=2), 'ok')
        viejo = [{'conclusion': 'success', 'url': 'u', 'fecha': AHORA - timedelta(days=4)}]
        self.assertEqual(self.estado(viejo, plazo=2), 'ausente')
        self.assertEqual(self.estado(viejo, plazo=9), 'ok')

    def test_recien_dado_de_alta_esta_por_estrenar(self):
        self.assertEqual(e.juzgar([], 9, AHORA, AHORA - timedelta(days=3))[0], 'por estrenar')
        self.assertEqual(e.juzgar([], 9, AHORA, AHORA - timedelta(days=10))[0], 'ausente')
        self.assertEqual(e.juzgar([], 9, AHORA, None)[0], 'ausente')
        viejo = [{'conclusion': 'success', 'url': 'u', 'fecha': AHORA - timedelta(days=12)}]
        self.assertEqual(e.juzgar(viejo, 9, AHORA, AHORA - timedelta(days=1))[0], 'ausente')

    def test_sin_horario_y_sin_ejecuciones_propias_no_se_juzga(self):
        self.assertEqual(self.estado([], plazo=None), 'por PR')

    def test_racha_y_ultimo_exito(self):
        _estado, datos = e.juzgar(runs('failure', 'failure', 'success'), 2, AHORA)
        self.assertEqual(datos['racha'], 2)
        self.assertEqual(datos['exito'], AHORA - timedelta(hours=49))


class InformeTests(unittest.TestCase):
    REGISTRO = {'departamentos': [
        {'id': 'a', 'nombre': 'A', 'mision': 'm', 'workflows': ['uno', 'dos', 'tres']},
        {'id': 'b', 'nombre': 'B', 'mision': 'm', 'workflows': [], 'vacante': 'nadie',
         'pendientes': [{'herramienta': 'Knip', 'motivo': 'x'}]}]}
    WORKFLOWS = {n: {'fichero': n + '.yml', 'eventos': set(), 'crons': ['5 5 * * *']} for n in ('uno', 'dos', 'tres')}

    def leer(self, fichero, _repo):
        if fichero == 'tres.yml':
            raise RuntimeError('gh no pudo leer tres.yml')
        return runs('success') if fichero == 'uno.yml' else runs('failure', 'failure', 'failure')

    def test_el_informe_nombra_a_los_caidos_y_las_vacantes(self):
        filas = e.medir(self.REGISTRO, self.WORKFLOWS, 'o/r', AHORA, self.leer)
        texto, malos = e.informe(filas, self.REGISTRO, AHORA)
        self.assertEqual(sorted(f['workflow'] for f in malos), ['dos', 'tres'])
        self.assertEqual({f['workflow']: f['estado'] for f in filas}, {'uno': 'ok', 'dos': 'rojo', 'tres': 'sin datos'})
        self.assertIn('| A | `dos` | rojo | 3 |', texto)
        self.assertIn('Knip, vacante', texto)

    def test_por_estrenar_no_es_caido_y_alta_solo_se_pide_sin_ejecuciones(self):
        pedidas = []

        def alta(fichero, _repo):
            pedidas.append(fichero)
            return AHORA - timedelta(hours=20)

        filas = e.medir(self.REGISTRO, self.WORKFLOWS, 'o/r', AHORA,
                        lambda f, _r: [] if f == 'dos.yml' else runs('success'), alta)
        _texto, malos = e.informe(filas, self.REGISTRO, AHORA)
        self.assertEqual(pedidas, ['dos.yml'])
        self.assertEqual({f['workflow']: f['estado'] for f in filas}['dos'], 'por estrenar')
        self.assertEqual(malos, [])

    def test_todo_verde_no_deja_caidos(self):
        filas = e.medir(self.REGISTRO, self.WORKFLOWS, 'o/r', AHORA, lambda _f, _r: runs('success'))
        texto, malos = e.informe(filas, self.REGISTRO, AHORA)
        self.assertEqual(malos, [])
        self.assertIn('en verde', texto)


if __name__ == '__main__':
    unittest.main()
