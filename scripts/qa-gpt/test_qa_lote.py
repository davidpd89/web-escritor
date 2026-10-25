"""Pruebas offline del lote EJECUTAR-ACTIONS (repo git local + remoto bare + GitHub simulado; sin red, sin GPT): python scripts/qa-gpt/test_qa_lote.py"""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qa_gpt as q, qa_lote as L

WF = "name: tool\\non:\\n  workflow_dispatch:\\n  pull_request:\\n    paths:\\n      - 'tests/**'\\njobs:\\n  t:\\n    steps:\\n      - run: |\\n          for f in tests/test-*.py; do python $f; done\\n".replace("\\n", "\n")
OK_PY = "print('ok')\n"
FAIL_PY = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self): self.assertEqual(0, 1, 'DEFECTO')\nunittest.main()\n"
INFRA_PY = "import sys; sys.stderr.write('Error: connect ECONNRESET 1.2.3.4\\n'); sys.exit(1)\n"
BROKEN_PY = "def x(:\n"


def g(*a, cwd):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, (a, r.stderr)
    return r.stdout.strip()


class FakeGh:
    """GitHub simulado: remoto en memoria, runs que avanzan con `tick()`."""
    def __init__(self): self.remote, self.runs_, self.n, self.caido, self.scope = {}, [], 100, False, {"repo", "workflow"}; self.dispatches = []; self.pushes = []; self.log_text = "AssertionError: boom"
    def _chk(self):
        if self.caido: raise L.GhError("HTTP 502 simulado")
    def ok(self): self._chk(); return True
    def scopes(self): return self.scope
    def remote_sha(self, rama): self._chk(); return self.remote.get(rama)
    def push(self, sha, rama): self._chk(); self.remote[rama] = sha; self.pushes.append((rama, sha))
    def runs(self, wf, rama): self._chk(); return [dict(r) for r in self.runs_ if r["wf"] == wf and r["rama"] == rama]
    def run(self, rid): self._chk(); return next(dict(r) for r in self.runs_ if r["databaseId"] == rid)
    def workflow_ref(self): return "main"
    def dispatch(self, wf, rama, ref=None, campos=None):
        self._chk(); self.n += 1; self.dispatches.append((wf, rama))
        titulo = f"QA GPT {campos['modo']} {campos['sha']}" if campos else wf
        self.runs_.append({"wf": wf, "rama": rama, "databaseId": self.n, "headSha": self.remote[rama], "status": "queued", "conclusion": None, "url": f"https://x/runs/{self.n}", "event": "workflow_dispatch", "displayTitle": titulo, "campos": campos})
    def runs_grupo(self, sha): self._chk(); return [dict(r) for r in self.runs_ if sha in (r.get("displayTitle") or "") and r["wf"] == L.GRUPO_WF]
    def resultados(self, rid):
        """resultados.json simulado: self.res_clase decide la clase de todos los tests del grupo (por defecto 'ok')."""
        self._chk(); r = next(r for r in self.runs_ if r["databaseId"] == rid)
        tests = [t.split(":", 1)[1] for t in (r["campos"] or {}).get("tests", "").split()]
        clase = getattr(self, "res_clase", "ok")
        return {"modo": r["campos"]["modo"], "resumen": {clase: len(tests)}, "tests": [{"ruta": t, "exe": "python", "rc": 0 if clase == "ok" else 1, "clase": clase, "salida": "AssertionError: boom" if clase == "hallazgo" else ""} for t in tests]}
    def log_failed(self, rid): return self.log_text
    def tick(self, concl="success"):
        for r in self.runs_:
            if r["status"] == "queued": r["status"] = "in_progress"
            elif r["status"] == "in_progress": r["status"], r["conclusion"] = "completed", concl


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True); t = Path(self.tmp.name)
        self.bare, self.src, q.STATE = t / "bare.git", t / "src", t / "state"
        q.DB_PATH = q.STATE / "e.db"; q.Lock.path = q.STATE / "worker.lock"; q.ROOT = self.src; q.WT = q.STATE / "wt"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.bare)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.src)], check=True)
        (self.src / ".github/workflows").mkdir(parents=True); (self.src / ".github/workflows/tool-tests.yml").write_text(WF); (self.src / "tests").mkdir()
        (self.src / "tests/test-base.py").write_text(OK_PY)
        g("add", "-A", cwd=self.src); g("commit", "-qm", "base", cwd=self.src); g("remote", "add", "origin", str(self.bare), cwd=self.src); g("push", "-q", "origin", "main", cwd=self.src); g("fetch", "-q", "origin", cwd=self.src)
        self.c = q.db(); self.gh = FakeGh(); self.out = []; self.n = 0
        self.cfg = {"poll_s": 0, "concurrencia": 2, "max_horas": 1, "node_modules": str(t / "no-nm"), "timeout_test_s": 60}

    def tearDown(self):
        self.c.close(); self.tmp.cleanup()

    def preparar(self, nombre, contenido, categoria="regresion", workflow="tool-tests.yml", ruta=None):
        """Crea rama gpt-qa/<nombre> con un commit de test y las filas ramas/propuestas como lo deja stage()."""
        self.n += 1; ruta = ruta or f"tests/test-{nombre}.py"; rama = f"gpt-qa/{nombre}"
        g("checkout", "-q", "-b", rama, "origin/main", cwd=self.src); (self.src / ruta).parent.mkdir(parents=True, exist_ok=True); (self.src / ruta).write_text(contenido); g("add", "-A", cwd=self.src); g("commit", "-qm", f"test {nombre}", cwd=self.src)
        sha = g("rev-parse", "HEAD", cwd=self.src); g("checkout", "-q", "main", cwd=self.src)
        datos = {"titulo": nombre, "categoria": categoria, "workflow": workflow, "ficheros_nuevos": [{"ruta": ruta, "contenido": contenido}]}
        self.c.execute("INSERT INTO propuestas(id,huella,area,titulo,datos,estado,rama,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?)", (self.n, nombre, f"zona:{nombre}", nombre, json.dumps(datos), "preparada", rama, q.now(), q.now()))
        self.c.execute("INSERT INTO ramas(rama,area,ruta,sha,estado) VALUES(?,?,?,?,?)", (rama, f"zona:{nombre}", "", sha, "preparada")); self.c.commit()
        return rama, sha, self.n

    def lote(self, gh=None, **cfg):
        return L.Lote(q, gh or self.gh, sleep=lambda s: self.gh.tick(), out=self.out.append, cfg={**self.cfg, **cfg})

    def estado(self, rama): return self.c.execute("SELECT estado FROM lote_items WHERE rama=? ORDER BY actualizado DESC", (rama,)).fetchone()[0]
    def prop(self, pid): return self.c.execute("SELECT estado FROM propuestas WHERE id=?", (pid,)).fetchone()[0]


class Lotes(Base):
    def test_cero_pendientes(self):
        self.assertEqual(self.lote().ejecutar(), 0)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM lote_items").fetchone()[0], 0); self.assertEqual(self.gh.pushes, [])

    def test_un_test_correcto_llega_a_actions_ok(self):
        rama, sha, pid = self.preparar("uno", OK_PY)
        self.lote().ejecutar()
        self.assertEqual(self.estado(rama), "actions_ok"); self.assertEqual(self.gh.pushes, [(rama, sha)]); self.assertEqual(self.gh.dispatches, [("tool-tests.yml", rama)])
        self.assertEqual(self.prop(pid), "ejecutada")
        self.assertEqual(g("rev-parse", "origin/main", cwd=self.src), g("rev-parse", "main", cwd=self.src))  # main intacto

    def test_varios_y_doble_pulsacion_no_duplica(self):
        for n in "abc": self.preparar(n, OK_PY)
        self.lote().ejecutar(); d1, p1 = list(self.gh.dispatches), list(self.gh.pushes)
        self.assertEqual(len(d1), 3)
        self.lote().ejecutar()  # segundo clic
        self.assertEqual(self.gh.dispatches, d1); self.assertEqual(self.gh.pushes, p1)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM lote_items").fetchone()[0], 3)

    def test_defecto_real_se_registra_con_evidencia_y_se_confirma_en_actions(self):
        rama, sha, pid = self.preparar("def", FAIL_PY, categoria="descubre_defecto"); self.gh.res_clase = "hallazgo"
        self.lote().ejecutar()
        it = self.c.execute("SELECT * FROM lote_items").fetchone()
        self.assertEqual(it["estado"], "defecto_demostrado"); self.assertEqual(len(self.gh.dispatches), 1); self.assertEqual(self.gh.dispatches[0][0], L.GRUPO_WF)
        self.assertEqual(self.prop(pid), "ejecutada")

    def test_regresion_que_falla_es_fallo_de_test_no_defecto(self):
        self.preparar("reg", FAIL_PY, categoria="regresion"); self.lote().ejecutar()
        self.assertEqual(self.c.execute("SELECT estado FROM lote_items").fetchone()[0], "fallo_test")

    def test_test_roto_de_sintaxis_es_fallo_de_test(self):
        self.preparar("rot", BROKEN_PY); self.lote().ejecutar()
        self.assertEqual(self.c.execute("SELECT estado FROM lote_items").fetchone()[0], "fallo_test")

    def test_infra_local_se_reintenta_y_queda_infra(self):
        self.preparar("inf", INFRA_PY); self.lote().ejecutar()
        it = self.c.execute("SELECT * FROM lote_items").fetchone(); self.assertEqual(it["estado"], "infra"); self.assertEqual(it["local_clase"], "infra")
        self.assertGreaterEqual(it["intentos"], 2)  # reintentos acotados

    def test_actions_falla_con_aserciones_en_regresion_es_actions_fallida(self):
        rama, _, _ = self.preparar("af", OK_PY); lo = self.lote(); lo.sleep = lambda s: self.gh.tick("failure"); lo.ejecutar()
        self.assertEqual(self.estado(rama), "actions_fallida")

    def test_actions_cancelado_es_infra(self):
        rama, _, _ = self.preparar("ac", OK_PY); lo = self.lote(); lo.sleep = lambda s: self.gh.tick("cancelled"); lo.ejecutar()
        self.assertEqual(self.estado(rama), "infra")

    def test_workflow_en_curso_no_se_relanza_y_se_reconcilia(self):
        rama, sha, _ = self.preparar("run", OK_PY)
        self.gh.remote[rama] = sha; self.gh.n = 500; self.gh.runs_.append({"wf": "tool-tests.yml", "rama": rama, "databaseId": 777, "headSha": sha, "status": "in_progress", "conclusion": None, "url": "u", "event": "workflow_dispatch"})
        self.lote().ejecutar()
        self.assertEqual(self.gh.dispatches, []); self.assertEqual(self.estado(rama), "actions_ok")
        self.assertEqual(json.loads(self.c.execute("SELECT runs FROM lote_items").fetchone()[0])["tool-tests.yml"]["id"], 777)

    def test_no_cableado_va_al_workflow_dedicado(self):
        rama, _, _ = self.preparar("nc", OK_PY, ruta="qa/otro-browser.py"); self.lote().ejecutar()
        self.assertEqual(self.estado(rama), "actions_ok"); self.assertEqual([d[0] for d in self.gh.dispatches], [L.GRUPO_WF])

    def test_rama_que_toca_workflows_sin_scope(self):
        rama, sha, _ = self.preparar("wf", OK_PY)
        g("checkout", "-q", rama, cwd=self.src); (self.src / ".github/workflows/tool-tests.yml").write_text(WF + "# x\n"); g("commit", "-qam", "wf", cwd=self.src)
        sha2 = g("rev-parse", "HEAD", cwd=self.src); g("checkout", "-q", "main", cwd=self.src)
        self.c.execute("UPDATE ramas SET sha=? WHERE rama=?", (sha2, rama)); self.c.execute("UPDATE propuestas SET datos=json_set(datos,'$.ficheros_modificados',json('[{\"ruta\":\".github/workflows/tool-tests.yml\"}]'))"); self.c.commit()
        self.gh.scope = {"repo"}; self.lote().ejecutar()
        it = self.c.execute("SELECT * FROM lote_items").fetchone(); self.assertEqual(it["estado"], "revision_humana"); self.assertIn("workflow", it["detalle"]); self.assertEqual(self.gh.pushes, [])

    def test_commit_que_toca_ficheros_no_declarados_se_rechaza(self):
        rama, sha, _ = self.preparar("sucio", OK_PY)
        g("checkout", "-q", rama, cwd=self.src); (self.src / "index.html").write_text("<html>"); g("add", "-A", cwd=self.src); g("commit", "-q", "--amend", "--no-edit", cwd=self.src)
        sha2 = g("rev-parse", "HEAD", cwd=self.src); g("checkout", "-q", "main", cwd=self.src); self.c.execute("UPDATE ramas SET sha=?", (sha2,)); self.c.commit()
        self.lote().ejecutar(); it = self.c.execute("SELECT * FROM lote_items").fetchone()
        self.assertEqual(it["estado"], "revision_humana"); self.assertIn("no declarados", it["detalle"]); self.assertEqual(self.gh.pushes, [])

    def test_github_caido_valida_local_y_reanuda_despues(self):
        rama, _, pid = self.preparar("gh", OK_PY); self.gh.caido = True
        self.lote().ejecutar()
        self.assertEqual(self.estado(rama), "local_ok"); self.assertEqual(self.c.execute("SELECT estado FROM lotes").fetchone()[0], "en_curso")  # no se pierde
        self.assertEqual(self.prop(pid), "aprobada")  # sin evidencia de Actions no se marca ejecutada
        self.gh.caido = False; self.lote().ejecutar()
        self.assertEqual(self.estado(rama), "actions_ok"); self.assertEqual(len(self.gh.dispatches), 1)

    def test_interrupcion_tras_push_sin_run_registrado_se_recupera_sin_duplicar(self):
        rama, sha, _ = self.preparar("int", OK_PY); lo = self.lote(); lo.abrir_lote(); it = lo.item(f"{rama}@{sha[:12]}")
        lo.validar_local(it)
        # el BAT murio justo despues de dispatch: estado `enviado` sin run id, pero el run existe en GitHub
        self.gh.remote[rama] = sha; self.gh.n = 900
        self.gh.runs_.append({"wf": "tool-tests.yml", "rama": rama, "databaseId": 901, "headSha": sha, "status": "in_progress", "conclusion": None, "url": "u", "event": "workflow_dispatch"})
        lo.set(it["clave"], "enviado", "simulado"); lo.c.close()
        self.lote().ejecutar()
        self.assertEqual(self.gh.dispatches, []); self.assertEqual(self.estado(rama), "actions_ok")

    def test_interrupcion_a_mitad_de_validacion_local_reanuda(self):
        rama, sha, _ = self.preparar("mid", OK_PY); lo = self.lote(); lid = lo.abrir_lote()
        lo.set(f"{rama}@{sha[:12]}", "validacion_local", "interrumpido"); lo.c.close()
        self.lote().ejecutar(); self.assertEqual(self.estado(rama), "actions_ok")
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM lotes").fetchone()[0], 1)  # mismo lote

    def test_lo_generado_durante_el_lote_queda_para_el_siguiente(self):
        rama1, _, _ = self.preparar("v1", OK_PY); lo = self.lote(); orig = lo.validar_local; nuevo = {}
        def mientras(it):
            if not nuevo: nuevo["r"] = self.preparar("v2", OK_PY)  # el servicio genera una propuesta nueva en pleno lote
            return orig(it)
        lo.validar_local = mientras; lo.ejecutar()
        self.assertEqual(self.estado(rama1), "actions_ok"); self.assertEqual(self.c.execute("SELECT COUNT(*) FROM lotes").fetchone()[0], 2)  # lo nuevo va a un lote posterior, no al abierto
        self.assertEqual(self.estado(nuevo["r"][0]), "actions_ok"); self.assertEqual(len(self.gh.dispatches), 2)
        self.lote().ejecutar(); self.assertEqual(len(self.gh.dispatches), 2)

    def test_misma_rama_con_sha_nuevo_es_item_nuevo_y_conserva_el_viejo(self):
        rama, sha, _ = self.preparar("re", OK_PY); self.lote().ejecutar()
        g("checkout", "-q", rama, cwd=self.src); (self.src / "tests/test-re2.py").write_text(OK_PY); g("add", "-A", cwd=self.src); g("commit", "-qm", "m", cwd=self.src)
        sha2 = g("rev-parse", "HEAD", cwd=self.src); g("checkout", "-q", "main", cwd=self.src)
        self.c.execute("INSERT INTO propuestas(id,huella,area,titulo,datos,estado,rama,creado,actualizado) VALUES(50,'h','a','t',?,?,?,?,?)",
                       (json.dumps({"categoria": "regresion", "ficheros_nuevos": [{"ruta": "tests/test-re2.py"}]}), "preparada", rama, q.now(), q.now()))
        self.c.execute("UPDATE ramas SET sha=?,estado='preparada' WHERE rama=?", (sha2, rama)); self.c.commit()
        self.lote().ejecutar()
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM lote_items").fetchone()[0], 2); self.assertEqual(len(self.gh.dispatches), 2)

    def test_lock_impide_dos_lotes_simultaneos(self):
        with L.LoteLock(q):
            (q.STATE / "lote.lock").write_text(f"{os.getpid() + 0} x")  # el propio pid se tolera; simulamos otro vivo con el padre
            (q.STATE / "lote.lock").write_text(f"{os.getppid()} x")
            if q.pid_alive(os.getppid()):
                with self.assertRaises(SystemExit): L.LoteLock(q).__enter__()

    def test_panel_resume_el_lote(self):
        self.gh.res_clase = "hallazgo"
        for n in ("p", "d"): self.preparar(n, OK_PY if n == "p" else FAIL_PY, categoria="regresion" if n == "p" else "descubre_defecto")
        self.lote().ejecutar(); txt = "\n".join(L.bloque_estado(q, self.c))
        for k in ("aprobados 1", "Defectos de producto demostrados: 1", "Escritos, sin ejecutar: 0", "Ultimo lote", "Ultima ejecucion"): self.assertIn(k, txt)


NL = chr(10)
REC_WF = NL.join(["on:", "  workflow_dispatch:", "  pull_request:", "    paths:", "      - 'qa/reading-market-url-parity-browser.mjs'", "jobs:", "  t:", "    steps:", "      - run: |", "          node qa/reading-commerce-browser.mjs", ""])
TEST11 = "qa/reading-market-url-parity-browser.mjs"

class Cableado(unittest.TestCase):
    def test_workflow_que_omite_el_test_se_rechaza_aunque_lo_liste_en_paths(self):
        self.assertEqual(L.workflows_que_ejecutan([TEST11], {"rec.yml": REC_WF}), [])

    def test_workflow_que_lo_ejecuta_se_acepta(self):
        wf = REC_WF + "          node qa/reading-market-url-parity-browser.mjs" + NL + ""
        self.assertEqual(L.workflows_que_ejecutan([TEST11], {"rec.yml": wf}), ["rec.yml"])

    def test_comentario_no_cuenta_como_ejecucion(self):
        wf = REC_WF + "          # node qa/reading-market-url-parity-browser.mjs" + NL + ""
        self.assertEqual(L.workflows_que_ejecutan([TEST11], {"rec.yml": wf}), [])

    def test_asterisco_suelto_no_da_falso_verde(self):
        wf = REC_WF + "          grep -r foo * || true" + NL + ""
        self.assertEqual(L.workflows_que_ejecutan([TEST11], {"rec.yml": wf}), [])

    def test_glob_concreto(self):
        self.assertTrue(L.glob_concreto("qa/reading-*.mjs", TEST11))
        self.assertFalse(L.glob_concreto("*", TEST11)); self.assertFalse(L.glob_concreto("*.mjs", TEST11))
        self.assertFalse(L.glob_concreto("qa/reading-*.py", TEST11))

    def test_sin_workflow_dispatch_no_vale(self):
        wf = REC_WF.replace("  workflow_dispatch:" + NL, "") + "          node " + TEST11 + NL
        self.assertEqual(L.workflows_que_ejecutan([TEST11], {"rec.yml": wf}), [])


class Entorno(Base):
    def test_entorno_url_apunta_al_puerto_propio(self):
        f = Path(self.tmp.name) / "t.mjs"; f.write_text("const u = process.env.BASE_URL || process.env.SITE_ORIGIN; process.env.HOME", encoding="utf-8")
        self.assertEqual(L.Lote.entorno_url(f, 4199), {"BASE_URL": "http://127.0.0.1:4199", "SITE_ORIGIN": "http://127.0.0.1:4199"})

    def test_puerto_libre_evita_el_rango_de_los_servicios_del_usuario(self):
        p = self.lote().puerto_libre(); self.assertTrue(4173 + 20 <= p < 4173 + 60)


class Autorizacion(Base):
    def test_lock_crea_la_carpeta_de_estado_si_falta(self):
        import shutil; self.c.close(); shutil.rmtree(q.STATE / "lote", ignore_errors=True)
        class Q: STATE = Path(self.tmp.name) / "nuevo" / "estado"; now = staticmethod(q.now); pid_alive = staticmethod(q.pid_alive)
        with L.LoteLock(Q): self.assertTrue((Q.STATE / "lote.lock").exists())
        self.assertFalse((Q.STATE / "lote.lock").exists()); self.c = q.db()

    def test_token_sin_permisos_no_se_reintenta_y_queda_en_revision_humana(self):
        rama, _, pid = self.preparar("auth", OK_PY)
        def push(sha, r): raise L.GhAuthError("HTTP 403: Resource not accessible by personal access token")
        self.gh.push = push; self.lote().ejecutar()
        self.assertEqual(self.estado(rama), "revision_humana"); self.assertEqual(self.gh.dispatches, [])
        self.assertNotEqual(self.prop(pid), "ejecutada")

    def test_panel_cuenta_cada_test_una_vez(self):
        for n in ("a", "b", "c"): self.preparar(n, OK_PY)
        self.lote().ejecutar(); txt = NL.join(L.bloque_estado(q, self.c))
        self.assertIn("aprobados 3", txt)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM lote_items WHERE estado='actions_ok'").fetchone()[0], 3)


class SalidaInmediata(unittest.TestCase):
    def test_log_redirigido_a_fichero_se_ve_al_instante(self):
        """Un proceso con stdout a fichero debe dejar cada linea escrita sin esperar al cierre (piloto con log vacio)."""
        d = tempfile.mkdtemp(); log = Path(d) / "o.log"
        code = f"import sys; sys.path.insert(0, {str(Path(__file__).parent)!r}); import qa_lote as L; L.salida_inmediata(); print('hola'); import time; time.sleep(8)"
        with open(log, "w") as f: p = subprocess.Popen([sys.executable, "-c", code], stdout=f, stderr=subprocess.STDOUT)
        try:
            for _ in range(40):
                if "hola" in log.read_text(): break
                import time; time.sleep(0.25)
            self.assertIn("hola", log.read_text())
        finally: p.kill()


class Clasificacion(unittest.TestCase):
    def test_clasificar(self):
        c = L.Lote.clasificar
        self.assertEqual(c(None, 0, "ok", "regresion"), "local_ok")
        self.assertEqual(c(None, 1, "AssertionError: x", "descubre_defecto"), "defecto_demostrado")
        self.assertEqual(c(None, 1, "AssertionError [ERR_ASSERTION]", "regresion"), "fallo_test")
        self.assertEqual(c(None, 1, "Error: Cannot find package 'playwright'", "regresion"), "sin_entorno")
        self.assertEqual(c(None, 1, "OSError: [WinError 1314] El cliente no dispone de un privilegio requerido", "regresion"), "sin_entorno")
        self.assertEqual(c(None, 1, "connect ECONNRESET", "regresion"), "infra")
        self.assertEqual(c(None, 1, "SyntaxError", "regresion"), "fallo_test")


class RunCmdInterrumpible(unittest.TestCase):
    def tearDown(self): L.ABORTAR = None

    def test_parada_suelta_el_test_en_curso_en_segundos(self):
        import time
        L.ABORTAR = lambda: True; t = time.monotonic()
        rc, out = L.run_cmd([sys.executable, "-c", "import time; time.sleep(60)"], tempfile.gettempdir(), timeout=120)
        self.assertEqual(rc, L.RC_ABORTADO); self.assertLess(time.monotonic() - t, 15); self.assertIn("ABORTADO", out)

    def test_sin_parada_devuelve_salida_y_timeout_sigue_funcionando(self):
        L.ABORTAR = lambda: False
        self.assertEqual(L.run_cmd([sys.executable, "-c", "print('ok')"], tempfile.gettempdir()), (0, "ok\n"))
        rc, out = L.run_cmd([sys.executable, "-c", "import time; time.sleep(30)"], tempfile.gettempdir(), timeout=2)
        self.assertEqual(rc, 124); self.assertIn("Timeout", out)


class SenalDeParadaReal(unittest.TestCase):
    def test_ctrl_break_a_un_proceso_con_test_largo_lo_detiene_y_lo_registra(self):
        """Senal real de consola (CTRL_BREAK en grupo propio): instalar_parada -> pedir_parada -> run_cmd suelta el test."""
        import signal, time
        if os.name != "nt": self.skipTest("senales de consola de Windows")
        aqui = Path(__file__).parent
        p = subprocess.Popen([sys.executable, "-u", str(aqui / "_parada_hijo.py")], cwd=aqui, env={**os.environ, "PYTHONPATH": str(aqui)},
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        try:
            self.assertIn("LISTO", p.stdout.readline()); time.sleep(2); t = time.monotonic()
            p.send_signal(signal.CTRL_BREAK_EVENT); out = p.communicate(timeout=30)[0]
            self.assertLess(time.monotonic() - t, 20); self.assertIn("PARADA solicitada", out); self.assertIn("RC 130 cierre de ventana", out)
        finally:
            if p.poll() is None: p.kill()


if __name__ == "__main__":
    unittest.main(verbosity=1)
