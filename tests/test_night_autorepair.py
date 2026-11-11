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


    def test_una_carpeta_huerfana_no_bloquea_el_worktree(self):
        # 10/11: quedó C:/GIT/wt-autorepair-<run> con solo el enlace a node_modules y sin registro en git;
        # `worktree add` falló cada hora con «already exists» y atlas no volvió a repararse.
        import os, subprocess
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); repo = d / 'repo'; repo.mkdir(); vivo = d / 'node_modules_vivo'; vivo.mkdir()
            (vivo / 'paquete.js').write_text('no se borra')
            git = lambda *a: subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t', *a], cwd=repo,
                                            check=True, capture_output=True)
            git('init', '-q'); (repo / 'a').write_text('1'); git('add', '.'); git('commit', '-qm', 'x')
            wt = d / 'wt-autorepair-1'; wt.mkdir()
            # Lo que dejó de verdad: el enlace propio y el de la línea base de local-ci, con su venv.
            base = wt / '.local' / 'local-ci' / 'main'; base.mkdir(parents=True); (base / 'venv.txt').write_text('x')
            for enlace in (wt / 'node_modules', base / 'node_modules'):
                if os.name == 'nt':
                    subprocess.run(['cmd', '/c', 'mklink', '/J', str(enlace), str(vivo)], check=True, capture_output=True)
                else:
                    enlace.symlink_to(vivo)
            original = na.sh
            na.sh = lambda args, cwd=None, **k: original(args, cwd=cwd or repo, **k)
            try:
                na.quitar_worktree(wt)
            finally:
                na.sh = original
            self.assertFalse(wt.exists())
            self.assertEqual((vivo / 'paquete.js').read_text(), 'no se borra')
            git('worktree', 'add', '-q', '-b', 'r', str(wt), 'HEAD')
            self.assertTrue((wt / 'a').exists())
            git('worktree', 'remove', '--force', str(wt))

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


class PublicacionesLocales(unittest.TestCase):
    """Los textos fallaron tres noches (09-11/11) sin que nadie lo viera: solo se vigilaban workflows de GitHub."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.tmp.name)
        self.log = self.carpeta / 'publish.log'
        self.log.write_text('construyendo\nAssertionError: 17 metas de más de 160 caracteres\n', encoding='utf-8')
        self.addCleanup(self.tmp.cleanup)

    def test_vigilado_deja_exito(self):
        with na.estado_local.vigilado('publicacion-textos', self.log, ['py', 'x.py', 'publish'], self.carpeta, self.carpeta):
            self.assertEqual(na.estado_local.leer('publicacion-textos', self.carpeta)['status'], 'in_progress')
        r = na.estado_local.leer('publicacion-textos', self.carpeta)
        self.assertEqual((r['status'], r['conclusion']), ('completed', 'success'))

    def test_vigilado_deja_fallo_con_registro_y_traza(self):
        with self.assertRaises(SystemExit):
            with na.estado_local.vigilado('publicacion-textos', self.log, ['py', 'x.py', 'publish'], self.carpeta, self.carpeta):
                raise SystemExit(1)
        r = na.estado_local.leer('publicacion-textos', self.carpeta)
        self.assertEqual(r['conclusion'], 'failure')
        self.assertIn('17 metas', r['registro'])
        self.assertIn('SystemExit', r['registro'])
        self.assertIn('17 metas', na.registro_fallo(r['databaseId'], run=r))

    def test_la_vigilancia_incluye_las_locales(self):
        with na.estado_local.vigilado('publicacion-amazon', self.log, ['py'], self.carpeta, self.carpeta):
            pass
        self.assertEqual(na.flujos_locales(self.carpeta), ['local:publicacion-amazon'])
        viejo, na.estado_local.LOCALES = na.estado_local.LOCALES, self.carpeta
        try:
            r = na.ultima_ejecucion('local:publicacion-amazon')
        finally:
            na.estado_local.LOCALES = viejo
        self.assertEqual(r['conclusion'], 'success')

    def test_decidir_entiende_la_fecha_local(self):
        r = {'status': 'completed', 'conclusion': 'failure', 'databaseId': 'x',
             'createdAt': (AHORA - dt.timedelta(hours=1)).isoformat(timespec='seconds')}
        self.assertEqual(na.decidir(r, None, AHORA, 0), 'relanzar')

    def test_rama_y_carpeta_validas(self):
        self.assertEqual(na.ident('local:publicacion-textos-2026-11-11T19:00:00+00:00'),
                         'local-publicacion-textos-2026-11-11T19-00-00-00-00')

    def test_relanzar_local_actualiza_a_main_y_lanza_el_mismo_comando(self):
        llamadas, lanzados = [], []
        sh, popen = na.sh, na.subprocess.Popen
        na.sh = lambda args, **kw: llamadas.append((args, kw.get('cwd')))
        na.subprocess.Popen = lambda argv, **kw: lanzados.append((argv, kw['cwd']))
        try:
            na.relanzar('local:publicacion-textos', {'argv': ['py', '-u', 'x.py', 'publish'], 'cwd': str(self.carpeta),
                                                      'registro_ruta': str(self.log)})
        finally:
            na.sh, na.subprocess.Popen = sh, popen
        self.assertEqual([a[:3] for a, _ in llamadas], [['git', 'fetch', '-q'], ['git', 'checkout', '-q']])
        self.assertEqual(lanzados, [(['py', '-u', 'x.py', 'publish'], self.carpeta)])
        self.assertIn('relanzada por la autorreparación', self.log.read_text(encoding='utf-8'))


class Historial(unittest.TestCase):
    """11/11: el segundo agente no sabía que el arreglo del primero ya estaba en main y repitió la hipótesis falsa."""

    def test_el_prompt_lleva_los_intentos_y_cuestiona_la_premisa(self):
        historial = [{'fecha': '2026-11-11T03:00', 'agente': 'claude', 'pr': 1270, 'titulo': 'Reconocer la propuesta del bot',
                      'resultado': 'mergeada; se relanza el flujo para comprobarla'}]
        p = na.prompt_reparacion('reading-catalogue-sync.yml', run(), 'Refusing to replace', historial, '\nPR abiertas: #1268')
        self.assertIn('PR #1270', p)
        self.assertIn('YA ESTÁ EN MAIN', p)
        self.assertIn('#1268', p)
        self.assertIn('falle sin tu arreglo', p)
        self.assertNotIn('YA ESTÁ EN MAIN', na.prompt_reparacion('x.yml', run(), 'r'))

    def test_registrar_intento(self):
        e = {}
        na.registrar_intento(e, {'pr': 7, 'agente': 'claude', 'titulo': 'T'}, run(), AHORA)
        self.assertFalse(e['pr_cerrada'])
        self.assertEqual(e['historial'][-1]['resultado'], 'PR abierta con auto-merge')
        na.anotar(e, 'CI rojo en la PR: python-tests')
        na.registrar_intento(e, {'fallido': True}, run(), AHORA)
        self.assertTrue(e['pr_cerrada'])
        self.assertNotIn('pr', e)
        self.assertEqual([h['resultado'][:7] for h in e['historial']], ['CI rojo', 'ninguna'])
        for _ in range(20):
            na.registrar_intento(e, {'sin_arreglo': 'es de GitHub', 'agente': 'codex'}, run(), AHORA)
        self.assertEqual(len(e['historial']), na.HISTORIAL_MAX)


class PrAtascada(unittest.TestCase):
    """Antes una PR de reparación en rojo dejaba el flujo en «esperar_pr» para siempre."""

    def pr(self, minutos, *checks):
        return {'createdAt': (AHORA - dt.timedelta(minutes=minutos)).isoformat().replace('+00:00', 'Z'),
                'statusCheckRollup': [{'name': n, 'status': s, 'conclusion': c} for n, s, c in checks]}

    def test_rojo_terminado_se_cierra(self):
        self.assertIn('python-tests', na.pr_atascada(self.pr(40, ('python-tests', 'COMPLETED', 'FAILURE'),
                                                             ('lint', 'COMPLETED', 'SUCCESS')), AHORA))

    def test_aun_corriendo_o_reciente_espera(self):
        self.assertEqual(na.pr_atascada(self.pr(40, ('a', 'COMPLETED', 'FAILURE'), ('b', 'IN_PROGRESS', None)), AHORA), '')
        self.assertEqual(na.pr_atascada(self.pr(10, ('a', 'COMPLETED', 'FAILURE')), AHORA), '')
        self.assertEqual(na.pr_atascada(self.pr(60, ('a', 'COMPLETED', 'SUCCESS')), AHORA), '')

    def test_caduca(self):
        self.assertTrue(na.pr_atascada(self.pr(na.PR_CADUCA_H * 60 + 1, ('b', 'IN_PROGRESS', None)), AHORA))


class Pasada(unittest.TestCase):
    def setUp(self):
        self.estado, self.hechos = {}, []
        guardar = {k: getattr(na, k) for k in ('cargar_estado', 'guardar_estado', 'actions_caido', 'ultima_ejecucion',
                                                'gh_json', 'sh', 'relanzar', 'avisar', 'log', 'ingesta_en_marcha',
                                                'fallo_de_infraestructura')}
        self.addCleanup(lambda: [setattr(na, k, v) for k, v in guardar.items()])
        na.cargar_estado = lambda: self.estado
        na.guardar_estado = lambda e: None
        na.actions_caido = lambda: ''
        na.log = lambda m: None
        na.ingesta_en_marcha = lambda: False
        na.relanzar = lambda f, r: self.hechos.append(('relanzar', f))
        na.avisar = lambda f, r, h, i=None: self.hechos.append(('avisar', f)) or 99
        na.sh = lambda args, **kw: self.hechos.append(tuple(args[:3]))

    def test_pr_mergeada_relanza_y_lo_anota(self):
        self.estado['local:publicacion-textos'] = {'pr': 5, 'historial': [{'resultado': 'PR abierta con auto-merge'}]}
        na.ultima_ejecucion = lambda f: run()
        na.gh_json = lambda *a: {'state': 'MERGED'}
        na.pasada(solo='local:publicacion-textos')
        self.assertIn(('relanzar', 'local:publicacion-textos'), self.hechos)
        self.assertTrue(self.estado['local:publicacion-textos']['historial'][-1]['resultado'].startswith('mergeada'))

    def test_pr_en_rojo_se_cierra_y_libera_el_flujo(self):
        self.estado['x.yml'] = {'pr': 5, 'historial': [{'resultado': 'PR abierta con auto-merge'}]}
        na.ultima_ejecucion = lambda f: run(status='in_progress')
        creada = (AHORA - dt.timedelta(hours=5)).isoformat()
        na.gh_json = lambda *a: {'state': 'OPEN', 'createdAt': creada, 'statusCheckRollup': []}
        na.pasada(solo='x.yml')
        self.assertIn(('gh', 'pr', 'close'), self.hechos)
        self.assertTrue(self.estado['x.yml']['pr_cerrada'])

    def test_agotado_avisa_una_vez_al_dia(self):
        hoy = dt.datetime.now(dt.timezone.utc)
        self.estado['x.yml'] = {'relanzado': (hoy - dt.timedelta(hours=3)).isoformat(),
                                'intentos': [hoy.isoformat()] * na.MAX_INTENTOS_DIA, 'pr_cerrada': True}
        na.ultima_ejecucion = lambda f: {**run(), 'createdAt': (hoy - dt.timedelta(hours=1)).isoformat()}
        na.fallo_de_infraestructura = lambda i: False
        na.pasada(solo='x.yml')
        na.pasada(solo='x.yml')
        self.assertEqual(self.hechos.count(('avisar', 'x.yml')), 1)
        self.assertEqual(self.estado['x.yml']['issue'], 99)


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


class AgenteSinEscritura(unittest.TestCase):
    """El agente no puede empujar: el push lo hace el orquestador tras la puerta local."""

    def test_el_agente_no_puede_empujar_y_el_orquestador_si(self):
        import os, subprocess
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            git = lambda *a, env=None, cwd=tmp / 'wt': subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True,
                                                                     env={**os.environ, **(env or {})})
            git('init', '-q', '--bare', str(tmp / 'remoto.git'), cwd=tmp)
            git('clone', '-q', str(tmp / 'remoto.git'), str(tmp / 'wt'), cwd=tmp)
            (tmp / 'wt' / 'a.txt').write_text('x')
            git('add', 'a.txt')
            git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x')
            agente = git('push', '-q', 'origin', 'HEAD:main', env=na.sin_escritura(tmp / 'gh'))
            self.assertNotEqual(agente.returncode, 0)
            self.assertEqual(git('push', '-q', 'origin', 'HEAD:main').returncode, 0)

    def test_gh_queda_sin_sesion(self):
        env = na.sin_escritura(Path(tempfile.mkdtemp()) / 'gh')
        self.assertEqual(env['GH_TOKEN'], '')
        self.assertTrue(Path(env['GH_CONFIG_DIR']).is_dir())
        self.assertEqual(list(Path(env['GH_CONFIG_DIR']).iterdir()), [])
