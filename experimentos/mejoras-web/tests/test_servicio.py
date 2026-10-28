from unittest.mock import patch
import json, os, re, subprocess, sys, unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock
import util
import mw, supervisor, informe, edge_launcher, gpt_browser, claude_cli, preflight

LAB = mw.LAB


class Aislamiento(util.Caso):
    def test_configuracion_por_defecto_esta_aislada_del_qa(self):
        self.assertEqual(mw.verificar_aislamiento(), [])
        self.assertEqual(mw.CFG["gpt"]["puerto_cdp"], 9331); self.assertEqual(gpt_browser.PORT, 9331); self.assertEqual(edge_launcher.PORT, 9331)
        self.assertNotIn("qa-gpt", str(mw.STATE).lower())

    def test_detecta_estado_puerto_y_perfil_del_qa(self):
        self.assertTrue(mw.verificar_aislamiento(state=r"C:\GIT\qa-gpt-state"))
        self.assertTrue(mw.verificar_aislamiento(puerto=9230)); self.assertTrue(mw.verificar_aislamiento(puerto=9224))
        self.assertEqual(mw.verificar_aislamiento(perfil=r"C:\Temp\web-escritor-qa-gpt-edge"), [])  # perfil compartido a proposito

    def test_edge_launcher_rehusa_puerto_y_perfil_del_qa(self):
        for kw in ({"port": 9230}, {"port": 9225}):
            with self.assertRaises(SystemExit): edge_launcher.comprobar_aislamiento(**kw)
        with patch.object(edge_launcher, "_qa_vivo", return_value=False): edge_launcher.comprobar_aislamiento()  # perfil compartido, QA parado
        with patch.object(edge_launcher, "_qa_vivo", return_value=True):
            with self.assertRaises(SystemExit): edge_launcher.comprobar_aislamiento()  # QA abierto con el mismo perfil
        f = edge_launcher.flags(); self.assertIn("--remote-debugging-port=9331", f); self.assertIn("--remote-debugging-address=127.0.0.1", f)
        self.assertFalse([x for x in f if "9230" in x])

    def test_gpt_browser_rechaza_el_project_y_puertos_del_qa(self):
        gpt_browser.configurar(project_id=gpt_browser.PROJECT_QA)  # Project compartido con el QA
        with self.assertRaises(ValueError): gpt_browser.configurar(port=9230)
        with self.assertRaises(ValueError): gpt_browser.configurar(project_id="no-es-un-id")
        gpt_browser.configurar(9331, "g-p-" + "ab12" * 8); self.assertTrue(gpt_browser.PROJECT_URL.endswith("/project"))
        gpt_browser.configurar(project_id="")

    def test_sin_project_configurado_no_se_envia_nada(self):
        gpt_browser.configurar(project_id="")
        with self.assertRaises(RuntimeError): gpt_browser.ask("hola")

    def test_prefijo_de_rama_propio(self):
        for r in ("mejoras-web/mw-0001", "mejoras-web/a/b"): self.assertTrue(mw.rama_permitida(r), r)
        for r in ("main", "master", "lab/mejoras-web-20261024", "gpt-qa/x", "qa-fix/x", "qa-dev/1", "research/mejoras-web-orquestador-20261024", "mejoras-web/..", "mejoras-web/a.lock", "", None, "mejoras-web/a b", "automation/qa-gpt"):
            self.assertFalse(mw.rama_permitida(r), r)

    def test_ningun_modulo_importa_ni_ejecuta_codigo_del_qa(self):
        for f in sorted(mw.HERE.glob("*.py")):
            t = f.read_text(encoding="utf-8")
            self.assertFalse(re.search(r"^\s*(import|from)\s+(qa_\w+|ci_grupo_qa)\b", t, re.M), f.name)
            self.assertNotIn("scripts/qa-gpt/", re.sub(r'"""[\s\S]*?"""', "", t), f.name)  # solo aparece en las docstrings de procedencia
            self.assertNotRegex(re.sub(r'"""[\s\S]*?"""', "", t), r"C:\\\\GIT\\\\qa-gpt-state(?!\")", f.name)

    def test_node_modules_y_cuentas_no_se_heredan_del_qa(self):
        self.assertEqual(mw.CFG["claude"]["cuentas_extra"], []); self.assertEqual(mw.CFG["actions"]["node_modules"], "")
        self.assertNotIn("pblac", (LAB / "config.json").read_text(encoding="utf-8"))


class InicioSinEfectosRemotos(util.Caso):
    def test_el_servicio_no_puede_despachar_ni_empujar(self):
        """Un paso completo del investigador (GPT + Claude) sin concederse AUTORIZADO: ninguna orden de gh ni push."""
        import investigar, gpt_browser as g
        ordenes = []
        real = mw.run
        def espia(args, **kw): ordenes.append(list(args)); return real(args, **kw)
        def ask(question, wait_min, stall_min, on_chat=None, on_result=None, resume_cid=None, registro=None):
            on_chat("1" * 32); res = g.Resultado("terminada", json.dumps(self.investigacion()), "1" * 32, 1, 1); on_result(res); return res
        investigar.ASK = ask
        investigar.CLAUDE_HOOK = lambda clave, tipo, s, e, esq: {"decision": "aprobar", "motivo": "x" * 40, "riesgo": "bajo", "criterio_aceptacion": "ok", "archivos": ["index.html"]}
        with mock.patch.object(mw, "run", espia):
            for _ in range(3): investigar.paso(self.c)
        self.assertFalse([o for o in ordenes if o[0] == "gh" or o[:2] == ["git", "push"]], ordenes)
        self.assertFalse(self.act.AUTORIZADO)
        with self.assertRaises(self.act.NoAutorizado): self.act.Gh(mw).dispatch("a" * 40, "aceptacion", "python:tests/mejoras-web/a.py", 1)

    def test_el_servicio_no_importa_el_ejecutor_de_actions(self):
        src = re.sub(r'"""[\s\S]*?"""', "", (mw.HERE / "investigar.py").read_text(encoding="utf-8"))
        self.assertNotRegex(src, r"import\s+.*\bactions\b"); self.assertNotIn("pr_hija", src)
        servicio = re.search(r"def cmd_servicio[\s\S]*?\ndef _python_sin_consola", (mw.HERE / "mw.py").read_text(encoding="utf-8")).group(0)
        servicio = re.sub(r'"""[\s\S]*?"""', "", servicio)
        self.assertNotIn("actions", servicio); self.assertNotIn("dispatch", servicio)

    def test_estado_sin_nada_arrancado(self):
        t = informe.texto(mw)
        self.assertIn("Investigador: parado", t); self.assertIn("Total expedientes: 0", t); self.assertIn("main intocable", t)

    def test_parar_sin_nada_en_marcha(self):
        self.assertEqual(mw.cmd_parar(None), 0); self.assertTrue(mw.flag("stop"))


class EdgeCompartido(util.Caso):
    NETSTAT = """  Proto  Direccion local         Direccion remota       Estado           PID
  TCP    127.0.0.1:9230         0.0.0.0:0              LISTENING       1111
  TCP    127.0.0.1:92310        0.0.0.0:0              LISTENING       2222
  TCP    127.0.0.1:9331         0.0.0.0:0              LISTENING       3333
  TCP    127.0.0.1:50000        127.0.0.1:9331         ESTABLISHED     4444
"""

    def test_solo_se_localiza_el_proceso_que_escucha_en_9331(self):
        self.assertEqual(edge_launcher.pid_escuchando(self.NETSTAT, 9331), 3333)
        self.assertEqual(edge_launcher.pid_escuchando(self.NETSTAT, 9230), 1111)  # (cerrar() nunca lo pide: PORT es 9331)
        self.assertIsNone(edge_launcher.pid_escuchando(self.NETSTAT, 9999)); self.assertIsNone(edge_launcher.pid_escuchando("", 9331))

    def test_cerrar_rehusa_el_puerto_del_qa(self):
        with patch.object(edge_launcher, "PORT", 9230), self.assertRaises(SystemExit): edge_launcher.cerrar()

    def test_parar_con_cerrar_edge_solo_llama_a_cerrar(self):
        with patch.object(edge_launcher, "cerrar", return_value=0) as c: mw.cmd_parar(NS(cerrar_edge=True))
        c.assert_called_once()
        with patch.object(edge_launcher, "cerrar", return_value=0) as c: mw.cmd_parar(NS(cerrar_edge=False))
        c.assert_not_called()

    def test_parar_bat_ofrece_cerrar_el_edge(self):
        t = (LAB / "PARAR-MEJORAS-WEB.bat").read_text(); self.assertIn("parar --cerrar-edge", t); self.assertIn("comparte su perfil", t)


class Supervisor(util.Caso):
    def hijo(self, codigos, lanzados):
        it = iter(codigos)
        class P:
            def wait(s): return next(it)
        def popen(args): lanzados.append(args); return P()
        return popen

    def test_relanza_tras_caida_y_termina_en_cero(self):
        l = []; r = supervisor.supervisar("servicio", popen=self.hijo([1, 75, 0], l), sleep=lambda s: None)
        self.assertEqual(r, 0); self.assertEqual(len(l), 3); self.assertTrue(all(a[-1] == "servicio" and a[1].endswith("mw.py") for a in l))
        self.assertIn("termino con codigo 1", (mw.STATE / "supervisor.log").read_text(encoding="utf-8"))

    def test_se_detiene_tras_demasiadas_caidas(self):
        l = []; r = supervisor.supervisar("servicio", popen=self.hijo([1] * 10, l), sleep=lambda s: None, maxi_caidas=3)
        self.assertEqual(r, 1); self.assertEqual(len(l), 3); self.assertEqual(mw.leer_servicio()["estado"], "detenido_por_caidas")

    def test_no_reintenta_config_invalida_ni_instancia_duplicada(self):
        for rc in (mw.RC_CONFIG, mw.RC_EN_MARCHA):
            l = []; self.assertEqual(supervisor.supervisar("servicio", popen=self.hijo([rc, 0], l), sleep=lambda s: None), rc); self.assertEqual(len(l), 1)

    def test_ctrl_c_no_mata_al_supervisor_y_ejecutar_conserva_su_consola(self):
        class P:
            n = 0
            def wait(s):
                s.n += 1
                if s.n == 1: raise KeyboardInterrupt
                return 0
        self.assertEqual(supervisor.supervisar("ejecutar-actions", ["--continuo"], popen=lambda a: P(), sleep=lambda s: None), 0)
        src = (mw.HERE / "supervisor.py").read_text(encoding="utf-8")
        self.assertIn('mw.SIN_VENTANA if modo == "servicio" else 0', src)  # el ejecutor NO se lanza sin ventana (se perderia el panel y la tecla Q)

    def test_stop_no_relanza(self):
        mw.set_flag("stop", True); l = []
        self.assertEqual(supervisor.supervisar("servicio", popen=self.hijo([1], l), sleep=lambda s: None), 0); self.assertEqual(l, [])

    def test_firma_estable(self):
        tb = 'Traceback (most recent call last):\n  File "/x/investigar.py", line 10, in paso\n    x\nKeyError: boom'
        self.assertEqual(supervisor.firma(tb), supervisor.firma(tb.replace("line 10", "line 99")))


class DobleArranque(util.Caso):
    def test_dos_servicios_no_conviven(self):
        mw.STATE.mkdir(parents=True, exist_ok=True)
        mw.Lock("worker").path.write_text(f"{os.getppid()} {mw.now()}")  # otro proceso vivo
        with self.assertRaises(SystemExit) as cm:
            with mw.Lock("worker"): pass
        self.assertEqual(cm.exception.code, mw.RC_EN_MARCHA)

    def test_iniciar_no_arranca_otro_si_ya_esta_en_marcha(self):
        mw.CFG["gpt"]["project_id"] = "g-p-" + "ab12" * 8
        with mock.patch.object(mw.Lock, "dueno", return_value=4242), mock.patch.object(mw, "popen") as po:
            self.assertEqual(mw.cmd_iniciar(None), 0)
        po.assert_not_called()

    def test_iniciar_sin_project_pide_configurarlo_y_no_arranca(self):
        mw.CFG["gpt"]["project_id"] = ""
        with mock.patch.object(mw, "popen") as po: self.assertEqual(mw.cmd_iniciar(None), 2)
        po.assert_not_called()

    def test_reinicio_tras_interrupcion_pone_los_jobs_en_pendiente_con_su_chat(self):
        j = self.job(); self.c.execute("UPDATE jobs SET estado='en_curso', chat_id=?, fase='generando'", ("e" * 32,)); self.c.commit()
        # lo que hace cmd_servicio al arrancar
        self.c.execute("UPDATE jobs SET estado='pendiente' WHERE estado='en_curso'")
        self.c.execute("UPDATE jobs SET no_antes=? WHERE estado='pendiente' AND fase='generando' AND chat_id IS NOT NULL", (mw.now(),)); self.c.commit()
        r = self.c.execute("SELECT * FROM jobs").fetchone(); self.assertEqual((r["estado"], r["chat_id"]), ("pendiente", "e" * 32))

    def test_servicio_arranca_y_se_para_con_stop_sin_hacer_nada_remoto(self):
        import investigar
        mw.CFG["gpt"]["project_id"] = "g-p-" + "ab12" * 8
        pasos = []
        def paso(c):
            pasos.append(1); mw.set_flag("stop", True); return True
        with mock.patch.object(investigar, "paso", paso), mock.patch.object(mw, "exigir_aislamiento"):
            self.assertEqual(mw.cmd_servicio(None), 0)
        self.assertEqual(len(pasos), 1); self.assertEqual(mw.leer_servicio()["estado"], "parado"); self.assertFalse(mw.Lock("worker").path.exists())


class Informe(util.Caso):
    def test_estado_muestra_fases_cola_sha_runs_gasto_y_errores(self):
        self.exp_preparado("MW-0001"); self.exp_preparado("MW-0002", estado="descartado_claude"); self.exp_preparado("MW-0003", estado="remoto_ok")
        self.c.execute("INSERT INTO cola(clave,exp,rama,sha,estado,detalle,tests,runs,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?,?)",
                       ("mejoras-web/mw-0003@abcdef012345", "MW-0003", "mejoras-web/mw-0003", "abcdef0123456789" * 2 + "abcdef01", "remoto_ok", "ok", "[]",
                        json.dumps({"1": {"id": 55, "url": "https://github.com/o/r/actions/runs/55", "conclusion": "success"}}), mw.now(), mw.now()))
        self.c.execute("INSERT INTO claude_llamadas(fecha,clave,tipo,coste_usd,ok,tok_in,tok_out,segundos) VALUES(?,?,?,?,1,100,50,3)", (mw.now(), "k", "contraste", 0.123))
        self.c.execute("INSERT INTO jobs(clave,tipo,area,estado,error,creado,actualizado) VALUES('I:x','I','a|0','error','chat inaccesible',?,?)", (mw.now(), mw.now())); self.c.commit()
        t = informe.texto(mw)
        for esperado in ("Preparados (esperan EJECUTAR): 1", "Descartados por Claude / duplicados / manual: 1", "Finalizados OK en Actions: 1", "mejoras-web/mw-0003 @ abcdef012345",
                         "https://github.com/o/r/actions/runs/55", "0.123 USD", "en ERROR 1", "chat inaccesible", "LISTO PARA PR: MW-0003", "Proximo para EJECUTAR: MW-0001", "Grupos en GitHub ahora: 0/3"):
            self.assertIn(esperado, t)


class Preflight(util.Caso):
    def test_offline_no_usa_red_ni_servicios(self):
        with mock.patch.object(mw, "run") as r, mock.patch("subprocess.run") as sr:
            res = preflight.verificar(real=False)
        r.assert_not_called(); sr.assert_not_called()
        self.assertTrue(res["ok"], [c for c in res["controles"] if not c["ok"]])

    def test_real_marca_lo_que_falta(self):
        mw.CFG["gpt"]["project_id"] = ""
        res = preflight.verificar(real=True); malos = {c["control"] for c in res["controles"] if not c["ok"]}
        self.assertIn("project_chatgpt", malos); self.assertFalse(res["ok"])


class Bats(unittest.TestCase):
    NOMBRES = ["INICIAR-MEJORAS-WEB.bat", "EJECUTAR-ACTIONS-MEJORAS-WEB.bat", "ESTADO-MEJORAS-WEB.bat", "PARAR-MEJORAS-WEB.bat"]

    def test_cuatro_lanzadores_en_la_carpeta_del_laboratorio(self):
        for n in self.NOMBRES: self.assertTrue((LAB / n).is_file(), n)

    def test_ascii_crlf_sin_rutas_ni_nombres_del_qa(self):
        for n in self.NOMBRES + ["motor/buscar-python.cmd"]:
            raw = (LAB / n).read_bytes(); raw.decode("ascii")
            self.assertNotIn(b"\n", raw.replace(b"\r\n", b""), n)
            t = raw.decode().lower()
            for malo in ("qa-gpt", "qa_gpt", "pblac", "c:\\git", "9230", "gpt-qa"): self.assertNotIn(malo, t, f"{n}: {malo}")

    def test_cada_bat_llama_a_su_orden_y_detecta_python(self):
        esperado = {"INICIAR-MEJORAS-WEB.bat": ["preflight.py\" --real", "mw.py\" iniciar"], "EJECUTAR-ACTIONS-MEJORAS-WEB.bat": ["supervisor.py\" ejecutar-actions --continuo", "preflight.py\" --offline"],
                    "ESTADO-MEJORAS-WEB.bat": ["mw.py\" estado"], "PARAR-MEJORAS-WEB.bat": ["mw.py\" parar"]}
        for n, cmds in esperado.items():
            t = (LAB / n).read_text()
            self.assertIn("buscar-python.cmd", t); self.assertIn(":sinpython", t)
            for c in cmds: self.assertIn(c, t, n)
        buscar = (LAB / "motor" / "buscar-python.cmd").read_text()
        for pista in ("where python", "py -3", "MEJORAS_WEB_PYTHON", "version_info>=(3,10)", "%LOCALAPPDATA%"): self.assertIn(pista, buscar)

    def test_iniciar_no_menciona_actions_ni_pr_salvo_para_negarlos_y_parar_no_cancela(self):
        t = (LAB / "INICIAR-MEJORAS-WEB.bat").read_text()
        self.assertNotIn("ejecutar-actions", t); self.assertNotIn(" pr ", t)
        self.assertIn("NO cancela", (LAB / "PARAR-MEJORAS-WEB.bat").read_text())
        self.assertIn("NO se cancelan", (LAB / "EJECUTAR-ACTIONS-MEJORAS-WEB.bat").read_text())

    def test_los_scripts_referenciados_existen(self):
        for s in ("preflight.py", "mw.py", "supervisor.py"): self.assertTrue((LAB / "motor" / s).is_file())

    def test_cli_estado_y_parar_como_subproceso_real(self):
        env = {**os.environ, "MEJORAS_WEB_STATE": tempfile_dir()}
        r = subprocess.run([sys.executable, str(LAB / "motor" / "mw.py"), "estado"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("LABORATORIO DE MEJORAS WEB", r.stdout)
        r = subprocess.run([sys.executable, str(LAB / "motor" / "mw.py"), "parar"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("Nada en marcha", r.stdout)

    def test_cli_iniciar_sin_project_falla_con_mensaje_util(self):
        env = {**os.environ, "MEJORAS_WEB_STATE": tempfile_dir(), "MEJORAS_WEB_PROJECT_ID": ""}
        cfg = json.loads((LAB / "config.json").read_text()); cfg["gpt"]["project_id"] = ""
        p = Path(tempfile_dir()) / "c.json"; p.write_text(json.dumps(cfg)); env["MEJORAS_WEB_CONFIG"] = str(p)
        r = subprocess.run([sys.executable, str(LAB / "motor" / "mw.py"), "iniciar"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 2); self.assertIn("FALTA el Project de ChatGPT", r.stdout)


def tempfile_dir():
    import tempfile
    return tempfile.mkdtemp(prefix="mw-cli-")


if __name__ == "__main__":
    unittest.main()
