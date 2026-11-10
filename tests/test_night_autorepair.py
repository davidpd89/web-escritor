import datetime as dt
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('night_autorepair', Path(__file__).resolve().parents[1] / 'scripts' / 'night-autorepair.py')
na = importlib.util.module_from_spec(spec)
spec.loader.exec_module(na)

AHORA = dt.datetime(2026, 11, 9, 7, 0, tzinfo=dt.timezone.utc)


def run(conclusion='failure', attempt=1, horas=2, status='completed'):
    return {'databaseId': 42, 'status': status, 'conclusion': conclusion, 'attempt': attempt, 'url': 'u',
            'createdAt': (AHORA - dt.timedelta(hours=horas)).isoformat().replace('+00:00', 'Z')}


class Decidir(unittest.TestCase):
    def test_primer_fallo_se_relanza(self):
        self.assertEqual(na.decidir(run(), None, AHORA, 0), 'relanzar')

    def test_segundo_fallo_se_repara(self):
        hace3h = (AHORA - dt.timedelta(hours=3)).isoformat()
        self.assertEqual(na.decidir(run(horas=2), {'relanzado': hace3h}, AHORA, 0), 'reparar')

    def test_espera_a_que_aparezca_el_relanzamiento(self):
        # La última sigue siendo la fallida de antes del dispatch: no se relanza otra vez ni se repara.
        hace1h = (AHORA - dt.timedelta(hours=1)).isoformat()
        self.assertEqual(na.decidir(run(horas=2), {'relanzado': hace1h}, AHORA, 0), 'nada')
        # Si el dispatch no apareció en 3 h, se vuelve a lanzar.
        hace4h = (AHORA - dt.timedelta(hours=4)).isoformat()
        self.assertEqual(na.decidir(run(horas=5), {'relanzado': hace4h}, AHORA, 0), 'relanzar')

    def test_limite_diario(self):
        hace3h = (AHORA - dt.timedelta(hours=3)).isoformat()
        self.assertEqual(na.decidir(run(horas=2), {'relanzado': hace3h}, AHORA, na.MAX_INTENTOS_DIA), 'agotado')

    def test_pr_abierta_espera(self):
        hace3h = (AHORA - dt.timedelta(hours=3)).isoformat()
        self.assertEqual(na.decidir(run(), {'pr': 7}, AHORA, 0), 'esperar_pr')
        self.assertEqual(na.decidir(run(horas=2), {'pr': 7, 'pr_cerrada': True, 'relanzado': hace3h}, AHORA, 0), 'reparar')

    def test_verde_olvida(self):
        self.assertEqual(na.decidir(run('success'), {'pr': 7}, AHORA, 0), 'olvidar')
        self.assertEqual(na.decidir(run('success'), None, AHORA, 0), 'nada')

    def test_no_toca_en_curso_cancelado_ni_viejo(self):
        self.assertEqual(na.decidir(run(status='in_progress'), None, AHORA, 0), 'nada')
        self.assertEqual(na.decidir(run('cancelled'), None, AHORA, 0), 'nada')
        self.assertEqual(na.decidir(run(horas=na.VENTANA_H + 1), None, AHORA, 0), 'nada')
        self.assertEqual(na.decidir(None, None, AHORA, 0), 'nada')


    def test_fallo_de_github_nunca_se_repara_con_ia(self):
        hace3h = (AHORA - dt.timedelta(hours=3)).isoformat()
        hace20m = (AHORA - dt.timedelta(minutes=20)).isoformat()
        # Sin infraestructura iría a reparar; con fallo de GitHub solo se reintenta, cada hora como mucho.
        self.assertEqual(na.decidir(run(horas=2), {'relanzado': hace3h}, AHORA, 0, infra=True), 'relanzar')
        self.assertEqual(na.decidir(run(horas=2), {'relanzado': hace20m}, AHORA, 0, infra=True), 'nada')
        self.assertEqual(na.decidir(run(horas=2), {'relanzado': hace3h}, AHORA, na.MAX_INTENTOS_DIA, infra=True), 'relanzar')


class CargaPerdida(unittest.TestCase):
    def test_sin_carga_hoy_se_lanza_una_vez(self):
        ayer = {'createdAt': '2026-11-08T00:20:00Z'}
        self.assertTrue(na.carga_perdida(ayer, AHORA, False))
        self.assertFalse(na.carga_perdida(ayer, AHORA, True))
        self.assertTrue(na.carga_perdida(ayer, AHORA.replace(hour=1), False))
        self.assertFalse(na.carga_perdida(ayer, AHORA.replace(hour=0, minute=50), False))
        self.assertFalse(na.carga_perdida({'createdAt': '2026-11-09T00:21:00Z'}, AHORA, False))


class Infraestructura(unittest.TestCase):
    def _jobs(self, jobs):
        from unittest import mock
        return mock.patch.object(na, 'gh_json', return_value={'jobs': jobs})

    def test_sin_trabajos_es_github(self):
        with self._jobs([]):
            self.assertTrue(na.fallo_de_infraestructura(1))

    def test_trabajo_sin_pasos_fallidos_es_github(self):
        with self._jobs([{'conclusion': 'failure', 'steps': []}]):
            self.assertTrue(na.fallo_de_infraestructura(1))

    def test_paso_fallido_es_codigo(self):
        with self._jobs([{'conclusion': 'failure', 'steps': [{'conclusion': 'success'}, {'conclusion': 'failure'}]}]):
            self.assertFalse(na.fallo_de_infraestructura(1))


class Filtros(unittest.TestCase):
    def test_cuota_agotada(self):
        for t in ("You've hit your limit · resets 3am", 'Error: 429 Too Many Requests', 'usage limit reached', "You've exceeded your quota"):
            self.assertTrue(na.sin_cuota(t), t)
        self.assertFalse(na.sin_cuota('AssertionError: 3 != 4'))

    def test_diff_que_apaga_el_sintoma(self):
        self.assertEqual(na.diff_valido('')[0], False)
        self.assertTrue(na.diff_valido('+++ b/x.py\n+    return fixed\n')[0])
        for malo in ('+      continue-on-error: true\n', '+  run: python x.py || true\n', '+@pytest.mark.skip\n', "+test.skip('x')\n"):
            self.assertFalse(na.diff_valido(malo)[0], malo)
        # Quitar un continue-on-error es justo lo contrario: se permite.
        self.assertTrue(na.diff_valido('-      continue-on-error: true\n')[0])

    def test_rotacion_de_cuentas(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual([a[0] for a in na.agentes(Path(d))], ['claude', 'claude-cuenta2', 'codex'])
            self.assertEqual(na.agentes(Path(d))[1][2], {'CLAUDE_CONFIG_DIR': d})
        self.assertEqual([a[0] for a in na.agentes(Path(d) / 'no-existe')], ['claude', 'codex'])

    def test_prompt_lleva_registro_y_reglas(self):
        p = na.prompt_reparacion('x.yml', {'url': 'https://r'}, 'KeyError: isbn')
        for trozo in ('x.yml', 'https://r', 'KeyError: isbn', 'AUTOREPAIR_SUMMARY.md', 'AUTOREPAIR_NOFIX.md', 'No hagas commit'):
            self.assertIn(trozo, p)

class PuertaDejaElArbol(unittest.TestCase):
    def test_lo_que_escribe_la_puerta_no_entra_en_el_arreglo(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            wt = Path(d)
            git = lambda *a: subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t', *a], cwd=wt, check=True,
                                            capture_output=True)
            git('init', '-q'); (wt / 'datos.json').write_text('1'); git('add', '.'); git('commit', '-qm', 'x')
            (wt / 'arreglo.py').write_text('fix'); (wt / 'datos.json').write_text('2'); git('add', '-A')
            (wt / 'datos.json').write_text('escrito por la puerta'); (wt / 'dist.html').write_text('build')
            na.dejar_como_el_indice(wt)
            self.assertEqual((wt / 'datos.json').read_text(), '2')  # el arreglo, no lo de la puerta
            self.assertEqual((wt / 'arreglo.py').read_text(), 'fix')
            self.assertFalse((wt / 'dist.html').exists())


class PuertaDelArreglo(unittest.TestCase):
    REGISTRO = (
        "subprocess.CalledProcessError: Command '('/opt/hostedtoolcache/Python/3.12/x64/bin/python', "
        "'scripts/check-reading-data.py')' returned non-zero exit status 1.\n"
        "FAIL: test_sin_gritos (test_reading_editorial_shouting.PublishedCatalogueTests.test_sin_gritos)\n")

    def test_pasos_fallidos_saca_el_script_y_el_modulo_de_test(self):
        self.assertEqual(na.pasos_fallidos(self.REGISTRO), [
            'python scripts/check-reading-data.py',
            'python -m unittest discover -s tests -p test_reading_editorial_shouting.py'])

    def test_decide_por_el_codigo_de_salida_no_por_el_texto(self):
        # 10/11: «0 fallos nuevos» en el texto con salida 1 no puede pasar, y salida 0 pasa diga lo que diga.
        self.assertFalse(na.veredicto_puerta(1, '0 fallos nuevos')[0])
        self.assertTrue(na.veredicto_puerta(0, '3 bien')[0])

    def test_sin_verificar_pasa_salvo_si_es_el_paso_que_fallo(self):
        ajeno = '  sin verificar (agotó 900 s): node qa/otra.mjs\n9 bien, 0 fallos nuevos, 1 sin verificar'
        propio = '  sin verificar (agotó 900 s): python scripts/check-reading-data.py\n9 bien, 0 fallos nuevos, 1 sin verificar'
        pasos = na.pasos_fallidos(self.REGISTRO)
        self.assertTrue(na.veredicto_puerta(2, ajeno, pasos)[0])
        self.assertFalse(na.veredicto_puerta(2, propio, pasos)[0])

    def test_el_siguiente_agente_parte_del_arreglo_anterior(self):
        p = na.prompt_continuar('BASE', 'claude', '## python x.py\nAssertionError')
        self.assertIn('Intento anterior (claude)', p)
        self.assertIn('AssertionError', p)
        # Un tercer intento sustituye la sección, no la acumula.
        p2 = na.prompt_continuar(p, 'claude-cuenta2', 'otro fallo')
        self.assertEqual(p2.count('## Intento anterior'), 1)
        self.assertTrue(p2.startswith('BASE'))


if __name__ == '__main__':
    unittest.main()


class CerrojoDeProceso(unittest.TestCase):
    """El cerrojo es del proceso: otro no entra mientras vive, y entra en cuanto muere, sin esperar caducidad."""

    SOSTENER = ('import importlib.util, sys, time\n'
                'spec = importlib.util.spec_from_file_location("na", sys.argv[1])\n'
                'na = importlib.util.module_from_spec(spec); spec.loader.exec_module(na)\n'
                'f = na.tomar_cerrojo(sys.argv[2]); print("dentro" if f else "fuera", flush=True)\n'
                'time.sleep(60)\n')

    def test_otro_proceso_no_entra_y_entra_al_morir_el_primero(self):
        import subprocess, sys
        script = Path(__file__).resolve().parents[1] / 'scripts' / 'night-autorepair.py'
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'lock'
            primero = subprocess.Popen([sys.executable, '-c', self.SOSTENER, str(script), str(ruta)],
                                       stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(primero.stdout.readline().strip(), 'dentro')
                self.assertIsNone(na.tomar_cerrojo(ruta))
            finally:
                primero.kill()
                primero.wait()
                primero.stdout.close()
            f = na.tomar_cerrojo(ruta)  # muerto sin borrar el fichero: se entra ya
            self.assertIsNotNone(f)
            f.close()

    def test_cerrar_lo_suelta(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'lock'
            f = na.tomar_cerrojo(ruta)
            self.assertIsNotNone(f)
            f.close()
            g = na.tomar_cerrojo(ruta)
            self.assertIsNotNone(g)
            g.close()
