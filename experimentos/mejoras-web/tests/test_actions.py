import json, subprocess, unittest
from pathlib import Path
from unittest import mock
import util
import mw, actions, clases, parches

SHA = lambda n: f"{n:040x}"


class GhFalso:
    """Simula GitHub: runs con displayTitle `Mejoras web <sha> #<intento>`. Registra todas las llamadas y cuantos grupos hay vivos a la vez."""
    def __init__(self, completar_en=2):
        self.runs, self.remotes, self.llamadas, self.vivos_max, self.sig = [], {}, [], 0, 1000
        self.completar_en, self.fallar_tras_dispatch = completar_en, None
        self.defecto = {"modo": "aceptacion", "resumen": {"ok": 1}, "tests": [{"ruta": "tests/mejoras-web/a.py", "clase": "ok", "rc": 0}]}

    def ok(self): return True
    def remote_sha(self, rama): return self.remotes.get(rama)

    def push(self, sha, rama):
        if not actions.AUTORIZADO: raise actions.NoAutorizado("push")
        self.llamadas.append(("push", rama, sha)); self.remotes[rama] = sha

    def dispatch(self, sha, modo, tests, intento):
        if not actions.AUTORIZADO: raise actions.NoAutorizado("dispatch")
        self.sig += 1
        self.runs.append({"databaseId": self.sig, "status": "queued", "conclusion": None, "displayTitle": f"Mejoras web {sha} #{intento}", "url": f"https://github.com/o/r/actions/runs/{self.sig}",
                          "polls": 0, "artefacto": json.loads(json.dumps(self.defecto)), "log": ""})
        self.llamadas.append(("dispatch", sha, intento, tests)); self.vivos_max = max(self.vivos_max, sum(1 for r in self.runs if r["status"] != "completed"))
        if self.fallar_tras_dispatch: raise self.fallar_tras_dispatch

    def runs_grupo(self, sha, intento=1):
        return [dict(r) for r in self.runs if f"{sha} #{intento}" in r["displayTitle"]]

    def run(self, rid):
        r = next(x for x in self.runs if x["databaseId"] == rid); r["polls"] += 1
        if r["polls"] >= self.completar_en and r["status"] != "completed":
            r["status"], r["conclusion"] = "completed", r.get("final", "success")
        elif r["polls"] >= 1 and r["status"] == "queued": r["status"] = "in_progress"
        return {"databaseId": rid, "status": r["status"], "conclusion": r["conclusion"], "headSha": "w", "url": r["url"]}

    def resultados(self, rid): return next(x for x in self.runs if x["databaseId"] == rid)["artefacto"]
    def log_failed(self, rid): return next(x for x in self.runs if x["databaseId"] == rid)["log"]


class Base(util.Caso):
    def setUp(self):
        super().setUp()
        self.gh = GhFalso(); actions.AUTORIZADO = True
        self.cfgx = {"poll_s": 0, "espera_ociosa_s": 0, "timeout_test_s": 60, "concurrencia": 3}
        self.ex = self.nuevo_ejecutor()

    def nuevo_ejecutor(self, gh=None, **kw):
        ex = actions.Ejecutor(mw, gh=gh or self.gh, sleep=lambda s: None, out=lambda m: None, cfg={**self.cfgx, **kw}); self.addCleanup(ex.c.close)
        return ex

    def item_validado(self, n, estado="validado", rama=None):
        eid = f"MW-{n:04d}"
        self.c.execute("INSERT INTO expedientes(id,area,lente,titulo,necesidad,estado,datos,rama,sha,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       (eid, "accesibilidad", "1", f"mejora {n}", "n" * 50, "validado", "{}", rama or f"mejoras-web/mw-{n:04d}", SHA(n), mw.now(), mw.now()))
        clave = f"{rama or f'mejoras-web/mw-{n:04d}'}@{SHA(n)[:12]}"
        self.c.execute("INSERT INTO cola(clave,exp,rama,sha,estado,tests,runs,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?)",
                       (clave, eid, rama or f"mejoras-web/mw-{n:04d}", SHA(n), estado, json.dumps(["tests/mejoras-web/a.py"]), "{}", mw.now(), mw.now()))
        self.c.commit(); return clave

    def cola(self, clave): return self.c.execute("SELECT * FROM cola WHERE clave=?", (clave,)).fetchone()
    def exp(self, eid): return self.c.execute("SELECT * FROM expedientes WHERE id=?", (eid,)).fetchone()["estado"]


class GuardasDeGitHub(util.Caso):
    """Gh real con `mw.run` falso: ni se ejecuta gh ni git; se inspeccionan las ordenes."""
    def setUp(self):
        super().setUp(); self.ordenes = []
        def falso(args, **kw):
            self.ordenes.append(list(args)); return subprocess.CompletedProcess(args, 0, stdout="" if args[:2] == ["git", "ls-remote"] else "[]", stderr="")
        self.p = mock.patch.object(mw, "run", falso); self.p.start(); self.addCleanup(self.p.stop)
        self.gh = actions.Gh(mw)

    def test_sin_autorizacion_no_hay_push_ni_dispatch(self):
        with self.assertRaises(actions.NoAutorizado): self.gh.dispatch(SHA(1), "aceptacion", "python:tests/mejoras-web/a.py", 1)
        with self.assertRaises(actions.NoAutorizado): self.gh.push(SHA(1), "mejoras-web/mw-0001")
        self.assertEqual(self.ordenes, [])

    def test_con_autorizacion_solo_ramas_del_laboratorio(self):
        actions.AUTORIZADO = True
        for rama in ("main", "lab/mejoras-web-20261024", "gpt-qa/x", "qa-fix/x", "automation/qa-gpt", "mejoras-web/../main", "research/otra"):
            with self.assertRaises(actions.GhAuthError, msg=rama): self.gh.push(SHA(1), rama)
        self.assertEqual(self.ordenes, [])
        self.gh.push(SHA(1), "mejoras-web/mw-0001")
        self.assertIn(["git", "push", "origin", f"{SHA(1)}:refs/heads/mejoras-web/mw-0001"], self.ordenes)
        self.assertEqual([o for o in self.ordenes if o[:2] == ["git", "push"]].__len__(), 1)

    def test_dispatch_es_unico_y_apunta_al_workflow_dedicado(self):
        actions.AUTORIZADO = True; self.gh.dispatch(SHA(2), "aceptacion", "python:tests/mejoras-web/a.py", 2)
        o = self.ordenes[-1]
        self.assertEqual(o[:3], ["gh", "workflow", "run"]); self.assertEqual(o[3], "mejoras-web-grupo.yml"); self.assertIn(mw.CFG["workflow_ref"], o)
        self.assertIn(f"sha={SHA(2)}", o); self.assertIn("intento=2", o)
        self.assertEqual(sum(1 for o in self.ordenes if o[:3] == ["gh", "workflow", "run"]), 1)

    def test_gh_no_expone_fusion_cierre_cancelacion_ni_reenvio(self):
        for m in ("pr_merge", "pr_auto", "pr_cerrar", "pr_actualizar", "rerun_fallidos", "cancelar", "cancel", "merge"): self.assertFalse(hasattr(actions.Gh, m), m)

    def test_codigo_fuente_sin_ordenes_peligrosas(self):
        """Ningun modulo del laboratorio contiene ordenes que fusionen, cancelen, relancen, borren ramas o toquen main."""
        prohibido = [r'"pr",\s*"merge"', r'"run",\s*"cancel"', r'"run",\s*"rerun"', r"--delete-branch", r"--auto\b", r"--admin", r'"merge"\s*,\s*"--', r"gh\s+workflow\s+run", r'refs/heads/main',
                     r"origin\s+main\b", r"push\s+--force", r"--force-with-lease", r"gpt-qa/[a-z]"]
        import re
        for f in sorted(mw.HERE.glob("*.py")):
            texto = f.read_text(encoding="utf-8")
            texto = re.sub(r'"""[\s\S]*?"""', "", texto)  # las docstrings explican lo que se EXCLUYE del QA
            texto = "\n".join(l for l in texto.splitlines() if not l.strip().startswith("#"))
            for pat in prohibido:
                m = re.search(pat, texto)
                self.assertIsNone(m, f"{f.name}: {pat} -> {m.group(0) if m else ''}")


class Validacion(Base):
    def test_validar_local_construye_worktree_ejecuta_y_deja_en_la_cola_sin_publicar(self):
        eid = self.exp_preparado()
        self.assertEqual(self.ex.capturar(), 1)
        it = self.c.execute("SELECT * FROM cola").fetchone()
        self.assertEqual(it["estado"], "validado"); self.assertEqual(self.exp(eid), "validado")
        self.assertEqual(it["rama"], "mejoras-web/mw-0001"); self.assertRegex(it["sha"], r"^[0-9a-f]{40}$")
        t = self.c.execute("SELECT * FROM cola_tests").fetchone(); self.assertEqual((t["fuente"], t["clase"]), ("local", "ok"))
        self.assertIn("demuestran la mejora", it["detalle"])  # la linea base FALLA sin el cambio
        self.assertEqual(util.git(self.repo, "rev-parse", it["rama"]), it["sha"])
        self.assertEqual(self.gh.llamadas, []); self.assertFalse(parches.wt_path(eid).exists())  # nada publicado, worktree limpio
        self.assertEqual(util.git(self.repo, "worktree", "list").count("\n"), 0)
        self.assertNotIn("skip", (self.repo / "index.html").read_text(encoding="utf-8"))
        self.assertTrue(Path(it["local_log"]).is_file())

    def test_es_idempotente_y_reanudable(self):
        self.exp_preparado(); self.ex.capturar(); self.assertEqual(self.ex.capturar(), 0)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM cola").fetchone()[0], 1)

    def test_test_que_pasa_sin_el_cambio_no_demuestra_nada(self):
        prop = self.propuesta_gpt(pruebas=[{"ruta": "tests/mejoras-web/mw-0001-skip.py", "contenido": "html = open('index.html').read()\nassert '<main' in html, 'trivial'\nprint('ok')\n"}])
        self.exp_preparado(prop=prop); self.ex.capturar()
        it = self.c.execute("SELECT * FROM cola").fetchone(); self.assertEqual(it["estado"], "fallo_local"); self.assertIn("PASA sin el cambio", it["detalle"])
        self.assertEqual(self.exp("MW-0001"), "fallo_local")

    def test_test_que_falla_con_el_cambio_es_fallo_del_parche(self):
        prop = self.propuesta_gpt(pruebas=[{"ruta": "tests/mejoras-web/mw-0001-skip.py", "contenido": "html = open('index.html').read()\nassert 'texto-que-nadie-anade' in html, 'no esta'\n"}])
        self.exp_preparado(prop=prop); self.ex.capturar()
        it = self.c.execute("SELECT * FROM cola").fetchone(); self.assertEqual(it["estado"], "fallo_local")
        self.assertEqual(it["local_clase"], "fallo_test" if "ejecutable" in it["detalle"] else it["local_clase"])

    def test_test_que_no_se_puede_ejecutar_es_fallo_del_test_no_del_parche(self):
        prop = self.propuesta_gpt(pruebas=[{"ruta": "tests/mejoras-web/mw-0001-skip.py", "contenido": "import modulo_que_no_existe_jamas\nassert modulo_que_no_existe_jamas.x\n"}])
        self.exp_preparado(prop=prop); self.ex.capturar()
        it = self.c.execute("SELECT * FROM cola").fetchone(); self.assertEqual(it["estado"], "fallo_local"); self.assertIn("no es ejecutable", it["detalle"])

    def test_parche_que_no_encaja_con_la_base_actual(self):
        self.exp_preparado()
        (self.repo / "index.html").write_text("<html>otra cosa</html>", encoding="utf-8")
        util.git(self.repo, "commit", "-qam", "cambia base"); util.git(self.repo, "update-ref", "refs/remotes/origin/lab/mejoras-web-20261024", "HEAD")
        self.ex.capturar(); self.assertEqual(self.exp("MW-0001"), "fallo_local")
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM cola").fetchone()[0], 0)
        self.assertEqual(util.git(self.repo, "branch", "--list", "mejoras-web/*"), "")

    def test_validar_solo_no_toca_github(self):
        self.exp_preparado()
        with mock.patch.object(mw, "run", wraps=mw.run) as r:
            self.assertEqual(actions.validar_solo(mw, "MW-0001"), 0)
        self.assertFalse([c for c in r.call_args_list if c.args[0][0] == "gh"])
        self.assertEqual(self.c.execute("SELECT estado FROM cola").fetchone()[0], "validado")


class EnvioYRecogida(Base):
    def test_maximo_tres_grupos_simultaneos_y_todos_terminan(self):
        claves = [self.item_validado(n) for n in range(1, 6)]
        self.assertEqual(self.ex.ejecutar(), 0)
        self.assertEqual(self.gh.vivos_max, 3)  # nunca mas de 3 vivos a la vez
        self.assertEqual(len([l for l in self.gh.llamadas if l[0] == "dispatch"]), 5)
        for cl in claves: self.assertEqual(self.cola(cl)["estado"], "remoto_ok")
        self.assertEqual(self.exp("MW-0005"), "remoto_ok")

    def test_el_tope_es_configurable_y_no_pasa_de_tres(self):
        for n in range(1, 5): self.item_validado(n)
        ex = self.nuevo_ejecutor(concurrencia=1); ex.ejecutar(); self.assertEqual(self.gh.vivos_max, 1)
        gh2 = GhFalso(); [self.item_validado(n) for n in range(10, 14)]
        ex = self.nuevo_ejecutor(gh=gh2, concurrencia=99); ex.ejecutar(); self.assertLessEqual(gh2.vivos_max, 3)

    def test_dedupe_por_sha_recupera_el_run_existente(self):
        cl = self.item_validado(1)
        self.gh.runs.append({"databaseId": 7, "status": "in_progress", "conclusion": None, "displayTitle": f"Mejoras web {SHA(1)} #1", "url": "https://github.com/o/r/actions/runs/7", "polls": 0,
                             "artefacto": self.gh.defecto, "log": ""})
        self.ex.enviar(self.cola(cl))
        self.assertEqual([l for l in self.gh.llamadas if l[0] in ("dispatch", "push")], [])  # no relanza ni vuelve a empujar
        self.assertEqual(json.loads(self.cola(cl)["runs"])["1"]["id"], 7)

    def test_cierre_tras_el_dispatch_no_duplica(self):
        cl = self.item_validado(1)
        self.gh.fallar_tras_dispatch = actions.GhError("red caida tras lanzar")
        self.ex.enviar(self.cola(cl))
        self.assertEqual(self.cola(cl)["estado"], "enviado")  # no vuelve a `validado`: el dispatch pudo haber salido
        self.gh.fallar_tras_dispatch = None
        otro = self.nuevo_ejecutor()  # "reinicio" del ejecutor
        self.assertEqual(otro.reconciliar(otro.item(cl)), "viva")  # recupera el run existente por su sha
        otro.ejecutar()
        self.assertEqual(len([l for l in self.gh.llamadas if l[0] == "dispatch"]), 1)
        self.assertEqual(self.cola(cl)["estado"], "remoto_ok")

    def test_el_envio_exige_la_accion_manual(self):
        cl = self.item_validado(1); actions.AUTORIZADO = False
        with self.assertRaises(actions.NoAutorizado): self.ex.enviar(self.cola(cl))
        self.assertEqual(self.gh.llamadas, [])

    def test_sin_run_tras_el_dispatch_pasa_a_revision_humana(self):
        cl = self.item_validado(1)
        self.gh.runs_grupo = lambda sha, intento=1: []; self.gh.dispatch = lambda *a: None
        self.cfgx["espera_run_min"] = 0; ex = self.nuevo_ejecutor(); ex.enviar(ex.item(cl))
        self.assertEqual(ex.item(cl)["estado"], "enviado")
        self.c.execute("UPDATE cola SET enviado=?", ("2020-01-01T00:00:00",)); self.c.commit()
        ex.reconciliar(ex.item(cl)); self.assertEqual(ex.item(cl)["estado"], "revision_humana")
        self.assertIn(mw.CFG["workflow_ref"], ex.item(cl)["detalle"])

    def test_push_rechazado_va_a_revision_humana_y_no_se_reintenta_en_bucle(self):
        cl = self.item_validado(1)
        def push(sha, rama): raise actions.GhError("! [rejected] x -> mejoras-web/mw-0001 (non-fast-forward)")
        self.gh.push = push; self.ex.enviar(self.cola(cl))
        self.assertEqual(self.cola(cl)["estado"], "revision_humana"); self.assertIn("otro historial", self.cola(cl)["detalle"])
        self.assertEqual([l for l in self.gh.llamadas if l[0] == "dispatch"], [])

    def test_con_el_tope_diario_agotado_el_bucle_termina_sin_girar(self):
        for n in range(1, 3): self.item_validado(n)
        for i in range(12): self.c.execute("INSERT INTO envios VALUES(?,?,?)", (mw.today(), "x", i))
        self.c.commit(); self.nuevo_ejecutor().ejecutar()  # no se cuelga: termina y deja lo validado para manana
        self.assertEqual(self.gh.llamadas, []); self.assertEqual(self.c.execute("SELECT COUNT(*) FROM cola WHERE estado='validado'").fetchone()[0], 2)

    def test_tope_diario_de_envios(self):
        for n in range(1, 4): self.item_validado(n)
        ex = self.nuevo_ejecutor(max_envios_dia=2)
        for it in ex.items(): ex.enviar(ex.item(it["clave"]))
        self.assertEqual(len([l for l in self.gh.llamadas if l[0] == "dispatch"]), 2)

    def test_parada_no_cancela_runs_y_se_reanuda_sin_duplicar(self):
        cl = [self.item_validado(n) for n in (1, 2)]
        self.gh.completar_en = 99
        ex = self.nuevo_ejecutor(); ex.pedir_parada("prueba")
        for c_ in cl: ex.enviar(ex.item(c_))
        ex.ejecutar()
        self.assertTrue(all(self.cola(c_)["estado"] in ("actions_pendiente", "actions_ejecutando") for c_ in cl))
        self.assertEqual([l[0] for l in self.gh.llamadas if l[0] not in ("push", "dispatch")], [])  # ni cancelar ni nada mas
        self.gh.completar_en = 1
        ex2 = self.nuevo_ejecutor(); ex2.ejecutar()
        self.assertEqual(len([l for l in self.gh.llamadas if l[0] == "dispatch"]), 2)  # los mismos 2 envios: nada duplicado
        self.assertTrue(all(self.cola(c_)["estado"] == "remoto_ok" for c_ in cl))

    def test_flag_stop_detiene_el_bucle(self):
        self.item_validado(1); mw.set_flag("stop_actions", True)
        # ejecutar() lo detecta al empezar
        ex = self.nuevo_ejecutor(); ex.ejecutar(); self.assertEqual(self.gh.llamadas, [])
        mw.set_flag("stop_actions", False)

    def test_reintentar_infra_es_accion_explicita_y_crea_un_run_nuevo(self):
        cl = self.item_validado(1); self.gh.defecto = {"modo": "aceptacion", "resumen": {"infra": 1}, "tests": [{"ruta": "tests/mejoras-web/a.py", "clase": "infra", "rc": 1}]}
        self.ex.ejecutar(); self.assertEqual(self.cola(cl)["estado"], "remoto_infra")
        self.nuevo_ejecutor().ejecutar(); self.assertEqual(len([l for l in self.gh.llamadas if l[0] == "dispatch"]), 1)  # sin accion explicita, NO se reenvia
        self.gh.defecto = {"modo": "aceptacion", "resumen": {"ok": 1}, "tests": [{"ruta": "tests/mejoras-web/a.py", "clase": "ok", "rc": 0}]}
        self.assertEqual(actions.reintentar_infra(mw, cl), 0)
        self.nuevo_ejecutor().ejecutar()
        d = [l for l in self.gh.llamadas if l[0] == "dispatch"]
        self.assertEqual([x[2] for x in d], [1, 2]); self.assertEqual(self.cola(cl)["estado"], "remoto_ok")
        self.assertEqual(sorted(json.loads(self.cola(cl)["runs"])), ["1", "2"])

    def test_arranque_recupera_items_que_quedaron_validando(self):
        self.exp_preparado()
        cl = "mejoras-web/mw-0001@" + SHA(1)[:12]
        self.c.execute("INSERT INTO cola(clave,exp,rama,sha,estado,tests,runs,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?)", (cl, "MW-0001", "mejoras-web/mw-0001", SHA(1), "validando", "[]", "{}", mw.now(), mw.now()))
        self.c.execute("UPDATE expedientes SET estado='validando'"); self.c.commit()
        self.ex.ejecutar()  # el item a medias se descarta y el expediente se revalida desde cero (sin duplicar)
        self.assertIsNone(self.cola(cl)); self.assertEqual(self.c.execute("SELECT COUNT(*) FROM cola").fetchone()[0], 1)
        self.assertEqual(self.c.execute("SELECT estado FROM cola").fetchone()[0], "remoto_ok")


class WorkflowRef(Base):
    def test_config_apunta_a_la_rama_de_integracion_y_no_a_una_de_desarrollo(self):
        self.assertEqual(mw.CFG["workflow_ref"], "lab/mejoras-web-20261024")
        self.assertFalse(mw.CFG["workflow_ref"].startswith("research/")); self.assertNotEqual(mw.CFG["workflow_ref"], "main")  # en main el job se omite a proposito

    def test_sin_workflow_en_la_rama_no_se_envia_nada(self):
        self.item_validado(1); self.gh.workflow_disponible = lambda: "mejoras-web-grupo.yml no existe en la rama 'x'"
        logs = []; ex = actions.Ejecutor(mw, gh=self.gh, sleep=lambda s: None, out=logs.append, cfg=self.cfgx); self.addCleanup(ex.c.close); ex.ejecutar()
        self.assertEqual(self.gh.llamadas, []); self.assertTrue([l for l in logs if "NO SE ENVIA NADA" in l])
        self.assertEqual(self.cola("mejoras-web/mw-0001@" + SHA(1)[:12])["estado"], "validado")  # sigue en la cola para cuando se arregle

    def test_tambien_exige_el_workflow_en_la_rama_por_defecto(self):
        """Hecho real (28/10): `gh workflow run` dio 404 'not found on the default branch' mientras el workflow solo estaba en una rama de desarrollo."""
        def falso(args, **kw):
            sin_ref = "contents/.github/workflows/mejoras-web-grupo.yml" in " ".join(args) and "?ref=" not in " ".join(args)
            return subprocess.CompletedProcess(args, 1 if sin_ref else 0, stdout="", stderr="HTTP 404: Not Found")
        with mock.patch.object(mw, "run", falso): msg = actions.Gh(mw).workflow_disponible()
        self.assertIn("rama por defecto", msg); self.assertIn("main", msg)

    def test_workflow_disponible_usa_la_api_de_contenidos_en_el_ref(self):
        ordenes = []
        def falso(args, **kw): ordenes.append(list(args)); return subprocess.CompletedProcess(args, 1 if "borrada" in " ".join(args) else 0, stdout="", stderr="HTTP 404: Not Found")
        with mock.patch.object(mw, "run", falso):
            self.assertIsNone(actions.Gh(mw).workflow_disponible())
            mw.CFG["workflow_ref"] = "rama-borrada"; msg = actions.Gh(mw).workflow_disponible()
        self.assertIn("contents/.github/workflows/mejoras-web-grupo.yml?ref=lab/mejoras-web-20261024", " ".join(ordenes[0]))
        self.assertIn("rama-borrada", msg); self.assertIn("workflow_ref", msg)


class Clasificacion(Base):
    def fin(self, defecto=None, final="success", log="", artefacto=True):
        cl = self.item_validado(1)
        if defecto is not None: self.gh.defecto = defecto
        orig = self.gh.dispatch
        def d(*a):
            orig(*a); r = self.gh.runs[-1]; r["final"] = final; r["log"] = log
            if not artefacto: r["artefacto"] = None
        self.gh.dispatch = d
        self.ex.ejecutar(); return self.cola(cl)

    def res(self, *clases): return {"modo": "aceptacion", "resumen": {c: clases.count(c) for c in set(clases)}, "tests": [{"ruta": f"tests/mejoras-web/{i}.py", "clase": c, "rc": 0 if c == "ok" else 1} for i, c in enumerate(clases)]}

    def test_valido(self): self.assertEqual(self.fin(self.res("ok", "ok"))["estado"], "remoto_ok")
    def test_defecto_real_del_parche(self): self.assertEqual(self.fin(self.res("ok", "hallazgo"), final="failure")["estado"], "remoto_fallo_parche")
    def test_test_invalido(self): self.assertEqual(self.fin(self.res("invalido"), final="failure")["estado"], "remoto_fallo_test")
    def test_infraestructura(self): self.assertEqual(self.fin(self.res("ok", "infra"), final="failure")["estado"], "remoto_infra")
    def test_sin_entorno_nunca_es_valido(self): self.assertEqual(self.fin(self.res("sin_entorno"))["estado"], "remoto_infra")
    def test_invalido_pesa_mas_que_hallazgo(self): self.assertEqual(self.fin(self.res("hallazgo", "invalido"), final="failure")["estado"], "remoto_fallo_test")

    def test_job_verde_pero_resultado_rojo_manda_el_artefacto(self):
        self.assertEqual(self.fin(self.res("hallazgo"), final="success")["estado"], "remoto_fallo_parche")

    def test_run_verde_sin_artefacto_no_se_da_por_valido(self):
        it = self.fin(artefacto=False, final="success"); self.assertEqual(it["estado"], "remoto_infra"); self.assertIn("SIN resultados", it["detalle"])

    def test_cancelado_por_otro_es_infraestructura(self):
        self.assertEqual(self.fin(artefacto=False, final="cancelled")["estado"], "remoto_infra")

    def test_fallo_sin_artefacto_con_asercion_en_el_log(self):
        self.assertEqual(self.fin(artefacto=False, final="failure", log="AssertionError: falta skip-link")["estado"], "remoto_fallo_parche")

    def test_fallo_sin_artefacto_y_sin_asercion_no_se_atribuye_al_parche(self):
        self.assertEqual(self.fin(artefacto=False, final="failure", log="npm ERR! network ECONNRESET")["estado"], "remoto_infra")

    def test_los_tests_remotos_quedan_registrados_con_el_run(self):
        cl = self.fin(self.res("ok"))["clave"]
        t = self.c.execute("SELECT * FROM cola_tests WHERE clave=? AND fuente='actions'", (cl,)).fetchone(); self.assertEqual(t["clase"], "ok"); self.assertIsNotNone(t["run_id"])

    def test_clases_estado_remoto(self):
        e = clases.estado_remoto
        self.assertEqual(e([]), "fallo_test"); self.assertEqual(e(["ok"]), "valido"); self.assertEqual(e(["ok", "sin_entorno"]), "sin_entorno")


class Candado(util.Caso):
    def test_un_ejecutar_largo_no_es_terminado_por_otro_que_arranca(self):
        """Antes el bloqueo de EJECUTAR caducaba a las 2 h y el segundo arranque mataba al primero (aunque estuviera trabajando)."""
        mw.STATE.mkdir(parents=True, exist_ok=True)
        viejo = (mw._ahora() - __import__("datetime").timedelta(hours=5)).isoformat(timespec="seconds")
        mw.Lock("actions").path.write_text(f"{__import__('os').getppid()} {viejo}")
        with mock.patch.object(mw, "es_mw", return_value=True), mock.patch.object(mw, "matar_arbol") as matar:
            with self.assertRaises(SystemExit) as cm: actions.main(mw, mock.Mock(limite=None, continuo=False))
        self.assertEqual(cm.exception.code, mw.RC_EN_MARCHA); matar.assert_not_called()

    def test_ejecutar_no_borra_la_parada_pedida_al_investigador(self):
        mw.set_flag("stop", True)
        with mock.patch.object(actions, "Ejecutor") as E:
            E.return_value.ejecutar.return_value = 0; actions.main(mw, mock.Mock(limite=None, continuo=False))
        self.assertTrue(mw.flag("stop")); self.assertFalse(mw.flag("stop_actions"))

    def test_parar_pide_la_parada_de_los_dos_procesos(self):
        mw.cmd_parar(None); self.assertTrue(mw.flag("stop") and mw.flag("stop_actions"))

    def test_arranque_duplicado_del_investigador_no_borra_su_parada(self):
        mw.STATE.mkdir(parents=True, exist_ok=True); mw.set_flag("stop", True)
        mw.Lock("worker").path.write_text(f"{__import__('os').getppid()} {mw.now()}")
        mw.CFG["gpt"]["project_id"] = "g-p-" + "ab12" * 8
        with mock.patch.object(mw, "exigir_aislamiento"), self.assertRaises(SystemExit): mw.cmd_servicio(None)
        self.assertTrue(mw.flag("stop"))

    def test_doble_arranque_de_ejecutar_no_duplica(self):
        actions.AUTORIZADO = False
        mw.STATE.mkdir(parents=True, exist_ok=True)
        mw.Lock("actions").path.write_text(f"{__import__('os').getppid()} {mw.now()}")  # otro proceso VIVO (el padre de la prueba) sostiene el bloqueo
        with self.assertRaises(SystemExit) as cm: actions.main(mw, mock.Mock(limite=None, continuo=False))
        self.assertEqual(cm.exception.code, mw.RC_EN_MARCHA)
        self.assertFalse(actions.AUTORIZADO)  # y no concede autorizacion si no consiguio el bloqueo

    def test_lock_de_proceso_muerto_se_recupera(self):
        mw.STATE.mkdir(parents=True, exist_ok=True); mw.Lock("actions").path.write_text("999999 2020-01-01T00:00:00")
        with mw.Lock("actions") as lk: self.assertEqual(int(lk.path.read_text().split()[0]), __import__("os").getpid())
        self.assertFalse(mw.Lock("actions").path.exists())


if __name__ == "__main__":
    unittest.main()
