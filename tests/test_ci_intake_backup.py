"""Cron de respaldo de la ingesta: carga solo si esta noche no hay otra carga en verde ni en curso."""
import importlib.util
import io
import os
import pathlib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ci_intake_backup', ROOT / 'scripts/ci_intake_backup.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class DecideTest(unittest.TestCase):
    def test_cron_principal_descartado_carga(self):
        # 07/11: el cron de las 00:17 no saltó; no hay ninguna ejecución esta noche.
        self.assertTrue(backup.decide([])[0])

    def test_carga_en_curso_no_duplica(self):
        self.assertFalse(backup.decide([{'id': 1, 'status': 'in_progress'}])[0])
        self.assertFalse(backup.decide([{'id': 1, 'status': 'queued'}])[0])

    def test_carga_en_verde_no_repite(self):
        self.assertFalse(backup.decide([{'id': 1, 'status': 'completed', 'intake': 'success'}])[0])

    def test_reloj_que_no_cargo_no_cuenta(self):
        # Otro respaldo que decidió no cargar termina en verde sin job intake: no es una carga hecha.
        self.assertTrue(backup.decide([{'id': 2, 'status': 'completed', 'intake': 'skipped'},
                                       {'id': 3, 'status': 'completed', 'intake': None}])[0])

    def test_cargas_fallidas_se_reintentan(self):
        self.assertTrue(backup.decide([{'id': 1, 'status': 'completed', 'intake': 'failure'},
                                       {'id': 2, 'status': 'completed', 'intake': 'cancelled'}])[0])

    def test_decide_la_ultima_carga(self):
        # Reintento que salió bien: no se repite.
        self.assertFalse(backup.decide([{'id': 1, 'status': 'completed', 'intake': 'failure'},
                                        {'id': 2, 'status': 'completed', 'intake': 'success'}])[0])
        # 08/11: lote encadenado fallido tras uno en verde → la cadena se retoma (orden de la API, del más nuevo).
        self.assertTrue(backup.decide([{'id': 7, 'status': 'completed', 'intake': None},
                                       {'id': 6, 'status': 'completed', 'intake': 'failure'},
                                       {'id': 5, 'status': 'completed', 'intake': 'success'}])[0])


class MainTest(unittest.TestCase):
    def run_main(self, side_effect):
        out, err = io.StringIO(), io.StringIO()
        env = {'GITHUB_REPOSITORY': 'o/r', 'GITHUB_TOKEN': 't', 'RUN_ID': '9'}
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(backup, 'api', side_effect=side_effect), \
                redirect_stdout(out), redirect_stderr(err):
            os.environ.pop('GITHUB_STEP_SUMMARY', None)
            self.assertEqual(backup.main(), 0)
        return out.getvalue().strip()

    def test_sin_api_carga(self):
        self.assertEqual(self.run_main(OSError('down')), 'run=true')

    def test_se_excluye_a_si_misma_y_lee_el_job_intake(self):
        def api(path, token, timeout=20):
            if '/workflows/' in path:
                return {'workflow_runs': [{'id': 9, 'status': 'in_progress'}, {'id': 5, 'status': 'completed'}]}
            self.assertIn('/runs/5/jobs', path)
            return {'jobs': [{'name': 'clock', 'conclusion': 'success'}, {'name': 'intake', 'conclusion': 'success'}]}
        self.assertEqual(self.run_main(api), 'run=false')

    def fake(self, runs, jobs):
        def api(path, token, timeout=20):
            if '/workflows/' in path:
                return {'workflow_runs': runs}
            return {'jobs': jobs[int(path.split('/runs/')[1].split('/')[0])]}
        return api

    def test_un_ensayo_no_cuenta_como_carga(self):
        """#1312: un dry_run deja el job intake en verde sin publicar; no puede ceder la noche."""
        runs = [{'id': 5, 'status': 'completed', 'display_title': backup.DRY_RUN_TITLE, 'head_branch': 'main'}]
        jobs = {5: [{'name': 'intake', 'conclusion': 'success', 'completed_at': '2026-11-14T00:30:00Z'}]}
        self.assertEqual(self.run_main(self.fake(runs, jobs)), 'run=true')
        runs[0].update(display_title='Reading catalogue intake', head_branch='fix/otra')
        self.assertEqual(self.run_main(self.fake(runs, jobs)), 'run=true')

    def test_dos_relojes_solapados_no_se_ceden_el_paso(self):
        """#1312: el más antiguo sin decidir bloquea al nuevo, pero el nuevo no bloquea al antiguo."""
        clock = [{'name': 'clock', 'status': 'in_progress'}]
        self.assertEqual(self.run_main(self.fake([{'id': 12, 'status': 'in_progress'}], {12: clock})), 'run=true')
        self.assertEqual(self.run_main(self.fake([{'id': 3, 'status': 'in_progress'}], {3: clock})), 'run=false')
        # Reloj ya decidido con el intake saltado: no bloquea.
        done = [{'name': 'clock', 'status': 'completed', 'conclusion': 'success'},
                {'name': 'intake', 'status': 'completed', 'conclusion': 'skipped'}]
        self.assertEqual(self.run_main(self.fake([{'id': 3, 'status': 'in_progress'}], {3: done})), 'run=true')
        # Intake en marcha: bloquea.
        active = [{'name': 'clock', 'status': 'completed'}, {'name': 'intake', 'status': 'in_progress'}]
        self.assertEqual(self.run_main(self.fake([{'id': 12, 'status': 'in_progress'}], {12: active})), 'run=false')

    def test_un_reintento_se_ordena_por_cuando_termino(self):
        """#1312: el reintento de una ejecución vieja conserva su id; manda la última en terminar."""
        runs = [{'id': 8, 'status': 'completed'}, {'id': 4, 'status': 'completed'}]
        jobs = {8: [{'name': 'intake', 'conclusion': 'failure', 'completed_at': '2026-11-14T01:00:00Z'}],
                4: [{'name': 'intake', 'conclusion': 'success', 'completed_at': '2026-11-14T02:00:00Z'}]}
        self.assertEqual(self.run_main(self.fake(runs, jobs)), 'run=false')

    def test_sin_respuesta_a_tiempo_carga(self):
        """#1312: sin plazo global, 50 ejecuciones x 20 s superaban los 2 minutos del job."""
        runs = [{'id': i, 'status': 'completed'} for i in range(1, 6)]
        clock = iter(range(0, 1000, 30))
        with mock.patch.object(backup.time, 'monotonic', lambda: next(clock)):
            self.assertEqual(self.run_main(self.fake(runs, {i: [] for i in range(1, 6)})), 'run=true')

    def test_workflow_tiene_respaldos_y_concurrencia_en_el_job(self):
        yaml = (ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8')
        for cron in ("'17 0 * * *'", "'47 1 * * *'", "'17 3 * * *'"):
            self.assertIn(f'cron: {cron}', yaml)
        self.assertIn('python3 scripts/ci_intake_backup.py', yaml)
        # El grupo va en el job intake: un respaldo en cola nunca sustituye a la carga encadenada pendiente.
        self.assertNotIn('\nconcurrency:', yaml)
        self.assertIn('    concurrency:\n      group: reading-catalogue-intake', yaml.replace('\r\n', '\n'))


if __name__ == '__main__':
    unittest.main()
