import re, subprocess, unittest
import util
import mw

COMMIT = "fe131c8ce6a663b54ab067ea5bc123318ececbb0"
ARCHIVOS = {"gpt_browser.py": "gpt_browser.py", "edge_launcher.py": "edge_launcher.py", "claude_cli.py": "qa_claude.py", "clases.py": "qa_clases.py", "ci_grupo.py": "ci_grupo.py",
            "actions.py": "qa_lote.py", "parches.py": "qa_pr.py", "supervisor.py": "qa_supervisor.py", "mw.py": "qa_gpt.py"}


class Procedencia(unittest.TestCase):
    def test_cada_modulo_cita_commit_y_blob_del_qa(self):
        for mod, origen in ARCHIVOS.items():
            t = (mw.HERE / mod).read_text(encoding="utf-8")
            self.assertIn("PROCEDENCIA", t, mod); self.assertIn(origen, t, mod)
            self.assertTrue(COMMIT in t or "fe131c8c" in t, mod)

    def test_los_blobs_citados_son_los_reales(self):
        r = subprocess.run(["git", "-C", str(mw.REPO), "rev-parse", f"{COMMIT}:scripts/qa-gpt/qa_gpt.py"], capture_output=True, text=True)
        if r.returncode: self.skipTest("el commit de referencia del QA no esta en este clon")
        doc = (mw.LAB / "PROCEDENCIA.md").read_text(encoding="utf-8")
        for blob in set(re.findall(r"`([0-9a-f]{40})`", doc)):
            if blob == COMMIT: continue
            t = subprocess.run(["git", "-C", str(mw.REPO), "cat-file", "-t", blob], capture_output=True, text=True)
            self.assertEqual(t.stdout.strip(), "blob", blob)
        for mod, origen in ARCHIVOS.items():
            real = subprocess.run(["git", "-C", str(mw.REPO), "rev-parse", f"{COMMIT}:scripts/qa-gpt/{origen}"], capture_output=True, text=True).stdout.strip()
            self.assertIn(real, doc, origen)
            self.assertIn(real, (mw.HERE / mod).read_text(encoding="utf-8"), mod)

    def test_el_codigo_literal_del_qa_sigue_ahi(self):
        """Las funciones adaptadas conservan el cuerpo del original (no son reescrituras): un trozo representativo de cada una."""
        src = lambda m: (mw.HERE / m).read_text(encoding="utf-8")
        self.assertIn("d = pg.evaluate(_BACKEND_JS, cid)", src("gpt_browser.py")); self.assertIn("def evaluar(d, after_user=True)", src("gpt_browser.py"))
        self.assertIn("INVALIDO.search(out): return \"invalido\"", src("clases.py"))
        self.assertIn("for cuenta in cuentas(cfg):", src("claude_cli.py"))
        self.assertIn("class Conn(sqlite3.Connection)", src("mw.py"))
        self.assertIn("def veredicto_remoto", src("actions.py")); self.assertIn("def instalar_parada", src("actions.py"))
        self.assertIn("'buscar' aparece {n} veces (debe ser 1)", src("parches.py"))


if __name__ == "__main__":
    unittest.main()
