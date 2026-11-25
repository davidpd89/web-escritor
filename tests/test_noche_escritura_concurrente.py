"""Dos escritores del libro de la noche a la vez (25/11, caso 13 de la revisión GPT).

La carga 1 muere por timeout; el segador (reading-catalogue-reaper.yml) lee el libro con su apunte en curso y, antes de
que guarde, el turno siguiente (carga 2) abre: cierra la 1 como corte y apunta la 2 en curso. Antes el segador
reintentaba el push con los bytes de su lectura vieja y borraba el apunte de la carga 2 (y despachaba un reintento de
más). Ahora cada intento rehace el cambio sobre el libro remoto. Remoto git real en un directorio temporal, sin red.
"""
import io
import json
import subprocess
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
import catalogo_estado  # noqa: E402
import noche  # noqa: E402

T0 = datetime(2026, 11, 25, 0, 21, tzinfo=timezone.utc)


def git(*args, cwd):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class EscrituraConcurrenteTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        git('init', '--bare', '-q', str(base / 'remote.git'), cwd=base)
        self.repos = {}
        for nombre in ('segador', 'carga2'):
            repo = base / nombre
            git('init', '-q', str(repo), cwd=base)
            git('remote', 'add', 'origin', str(base / 'remote.git'), cwd=repo)
            self.repos[nombre] = repo

    def en(self, nombre):
        return mock.patch.multiple(catalogo_estado, ROOT=self.repos[nombre], WORK=self.repos[nombre] / '.local/x')

    def accion(self, nombre, accion, now, run, **args):
        datos = SimpleNamespace(**{'motivo': 'cron', 'resultado': 'failure', 'run_muerto': 0, 'intento_muerto': 1,
                                   **args})
        with self.en(nombre), mock.patch.object(noche, '_codigo', return_value='C'), \
                mock.patch.object(noche, '_head', return_value='sha'), \
                mock.patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': '', 'RUNNER_TEMP': ''}), \
                redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            rc = noche.ACCIONES[accion](now, run, 1, datos)
        return rc, out.getvalue()

    def libro(self):
        with self.en('segador'):
            return noche.leer()

    def test_el_segador_no_borra_el_apunte_de_la_carga_que_abrio_entretanto(self):
        self.accion('carga2', 'abrir', T0, 1)  # la carga 1 abre y muere sin cerrar
        leer_real = noche.leer

        def leer_y_que_abra_la_siguiente():
            libro = leer_real()  # el segador ya tiene su lectura (carga 1 en curso)...
            if not getattr(leer_y_que_abra_la_siguiente, 'hecho', False):
                leer_y_que_abra_la_siguiente.hecho = True
                self.assertEqual(self.accion('carga2', 'abrir', T0 + timedelta(hours=4), 2)[1], 'cargar=true\n')
            return libro  # ...y la carga 2 abre antes de que guarde

        with mock.patch.object(noche, 'leer', side_effect=leer_y_que_abra_la_siguiente):
            rc, _ = self.accion('segador', 'huerfana', T0 + timedelta(hours=4), 0, run_muerto=1)
        self.assertEqual(rc, 1, 'la carga 2 ya la cerró como corte: el segador no despacha otro reintento')
        intentos = [(i['run'], i['resultado']) for i in self.libro()['intentos']]
        self.assertEqual(intentos, [(1, 'fallido'), (2, 'en_curso')])

    def test_sin_carrera_el_segador_sigue_recogiendo(self):
        self.accion('carga2', 'abrir', T0, 1)
        rc, _ = self.accion('segador', 'huerfana', T0 + timedelta(hours=4), 0, run_muerto=1)
        self.assertEqual(rc, 0)
        self.assertEqual([(i['run'], i['resultado']) for i in self.libro()['intentos']],
                         [(1, 'fallido'), (None, 'pendiente')])

    def test_dos_cierres_a_la_vez_no_se_pisan(self):
        """Clase entera, no solo el segador: cualquier escritura reintentada rehace su cambio sobre lo remoto."""
        self.accion('carga2', 'abrir', T0, 1)
        leer_real = noche.leer

        def leer_y_despachar():
            libro = leer_real()
            if not getattr(leer_y_despachar, 'hecho', False):
                leer_y_despachar.hecho = True
                with self.en('segador'):
                    remoto = noche.pendiente(leer_real(), T0 + timedelta(minutes=5), 'cadena')
                    noche.escribir(remoto, 'otro escritor')
            return libro

        with mock.patch.object(noche, 'leer', side_effect=leer_y_despachar):
            self.accion('carga2', 'cerrar', T0 + timedelta(minutes=80), 1, resultado='success')
        self.assertEqual([(i['motivo'], i['resultado']) for i in self.libro()['intentos']],
                         [('cron', 'publicado'), ('cadena', 'pendiente')])


if __name__ == '__main__':
    unittest.main()
