import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
import util
import mw, ci_grupo, clases

MOTOR = mw.HERE


class Validacion(unittest.TestCase):
    def test_rutas_admitidas(self):
        for t in ("python:tests/mejoras-web/a.py", "node:tests/mejoras-web/b.mjs", "node:tests/mejoras-web/sub/c.js"): self.assertIsNotNone(ci_grupo.validar(t), t)
        for t in ("python:tests/otro/a.py", "python:../a.py", "bash:tests/mejoras-web/a.sh", "python:/abs/a.py", "python:tests/mejoras-web/a.mjs", "node:tests/mejoras-web/a.py",
                  "python:tests/mejoras-web/a;rm -rf x.py", "python:tests/mejoras-web/../../x.py", "python:scripts/qa-gpt/qa_gpt.py"): self.assertIsNone(ci_grupo.validar(t), t)


class Clasificacion(unittest.TestCase):
    def test_clases(self):
        c = clases.clasificar_salida
        self.assertEqual(c(0, "ok"), "ok"); self.assertEqual(c(0, "SIN_ENTORNO: x"), "sin_entorno")
        self.assertEqual(c(1, "Traceback...\nAssertionError: falta"), "hallazgo")
        self.assertEqual(c(1, "ModuleNotFoundError: No module named 'x'\nassert"), "invalido")  # un import roto no es un hallazgo aunque cite assert
        self.assertEqual(c(1, "SyntaxError: invalid"), "invalido"); self.assertEqual(c(1, "npm ERR! network ECONNRESET"), "infra")
        self.assertEqual(c(124, "TimeoutExpired tras 300s"), "infra"); self.assertEqual(c(1, "algo raro sin asercion"), "invalido")
        self.assertEqual(c(1, "Cannot find package 'playwright'"), "sin_entorno")

    def test_estado_remoto_precedencia(self):
        e = clases.estado_remoto
        self.assertEqual(e(["ok", "ok"]), "valido"); self.assertEqual(e(["ok", "hallazgo"]), "fallo_parche"); self.assertEqual(e(["hallazgo", "invalido"]), "fallo_test")
        self.assertEqual(e(["infra", "hallazgo"]), "infra"); self.assertEqual(e(["sin_entorno", "ok"]), "sin_entorno"); self.assertEqual(e([]), "fallo_test")


class Runner(unittest.TestCase):
    """Ejecuta ci_grupo.main de verdad (subprocesos reales de Python) en un repo temporal."""
    def run_grupo(self, ficheros, modo="aceptacion"):
        d = Path(tempfile.mkdtemp(prefix="mw-ci-")); (d / "tests" / "mejoras-web").mkdir(parents=True)
        for n, c in ficheros.items(): (d / "tests" / "mejoras-web" / n).write_text(c, encoding="utf-8")
        out = d / "resultados.json"; cwd = os.getcwd(); os.chdir(d)
        try: rc = ci_grupo.main(["ci_grupo.py", str(out), modo, " ".join(f"python:tests/mejoras-web/{n}" for n in ficheros)])
        finally: os.chdir(cwd)
        return rc, json.loads(out.read_text(encoding="utf-8"))

    def test_todo_ok_exit_0(self):
        rc, r = self.run_grupo({"a.py": "assert 1 + 1 == 2\nprint('ok')\n"}); self.assertEqual(rc, 0); self.assertEqual(r["resumen"], {"ok": 1}); self.assertEqual(r["modo"], "aceptacion")

    def test_asercion_fallida_es_rojo_y_hallazgo(self):
        rc, r = self.run_grupo({"a.py": "assert 1 == 2, 'no'\n", "b.py": "print('ok')\n"}); self.assertEqual(rc, 1)
        self.assertEqual({t["ruta"].split("/")[-1]: t["clase"] for t in r["tests"]}, {"a.py": "hallazgo", "b.py": "ok"})

    def test_test_roto_es_invalido_y_rojo(self):
        rc, r = self.run_grupo({"a.py": "import modulo_inexistente_xyz\n"}); self.assertEqual(rc, 1); self.assertEqual(r["tests"][0]["clase"], "invalido")

    def test_argumentos_invalidos_no_ejecutan_nada_y_escriben_resultados(self):
        d = Path(tempfile.mkdtemp()); out = d / "r.json"
        self.assertEqual(ci_grupo.main(["x", str(out), "exploratorio", "python:tests/mejoras-web/a.py"]), 2)
        self.assertEqual(ci_grupo.main(["x", str(out), "aceptacion", "python:/etc/passwd"]), 2)
        self.assertIn("argumentos_invalidos", json.loads(out.read_text())["resumen"])

    def test_resultados_solo_los_escribe_el_driver_y_la_salida_se_recorta(self):
        rc, r = self.run_grupo({"a.py": "print('x' * 9000)\nassert False, 'y'\n"}); self.assertLessEqual(len(r["tests"][0]["salida"]), 4000)


try:
    import yaml  # noqa: F401
except ImportError:  # pip install pyyaml (en el runner de Actions de la web no viene con setup-python)
    yaml = None


@unittest.skipIf(yaml is None, "falta pyyaml")
class Workflow(unittest.TestCase):
    WF = mw.REPO / ".github" / "workflows"

    def test_workflows_del_laboratorio_solo_manuales(self):
        import yaml
        for n in ("mejoras-web-grupo.yml", "mejoras-web-preview.yml", "lab-mejoras-offline.yml"):
            d = yaml.safe_load((self.WF / n).read_text(encoding="utf-8")); on = d.get("on") or d.get(True)
            self.assertEqual(list(on), ["workflow_dispatch"], n)
        g = yaml.safe_load((self.WF / "mejoras-web-grupo.yml").read_text(encoding="utf-8"))
        self.assertEqual(list((g.get("on") or g.get(True))["workflow_dispatch"]["inputs"]), ["sha", "modo", "tests", "intento"])
        self.assertEqual(g["permissions"], {"contents": "read"}); self.assertIn("#${{ inputs.intento }}", g["run-name"]); self.assertIn("${{ inputs.sha }}", g["run-name"])
        pasos = " ".join(str(s) for s in g["jobs"]["grupo"]["steps"])
        for prohibido in ("pa11y", "lighthouse", "reflow", "visual", "gh workflow run", "gh run rerun"): self.assertNotIn(prohibido, pasos.lower())
        self.assertIn("mejoras-web-resultados", pasos)

    def test_vista_previa_no_toca_pages_ni_produccion_y_exige_confirmacion(self):
        import yaml
        t = (self.WF / "mejoras-web-preview.yml").read_text(encoding="utf-8"); d = yaml.safe_load(t)
        self.assertEqual(d["permissions"], {"contents": "read"}); self.assertNotIn("pages: write", t); self.assertNotIn("deploy-pages", t.replace("deploy-pages.yml ni", ""))
        self.assertIn("PUBLICAR-PREVIEW", d["jobs"]["preview"]["if"]); self.assertIn("noindex", t)

    def test_los_commits_del_laboratorio_no_disparan_ningun_workflow_por_push(self):
        """Simula GitHub: ¿algun workflow con `push` coincide con la rama de desarrollo y los ficheros del laboratorio? (cascada de CI)"""
        import glob, re, yaml
        rama = "research/mejoras-web-motor-qa-20261027"
        ficheros = [str(p.relative_to(mw.REPO)).replace("\\", "/") for p in (mw.LAB).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        ficheros += [f".github/workflows/{n}" for n in ("mejoras-web-grupo.yml", "mejoras-web-preview.yml", "lab-mejoras-offline.yml")]
        pm = lambda p, f: re.fullmatch(re.escape(p).replace(r"\*\*", ".*").replace(r"\*", "[^/]*"), f) is not None
        disparan = []
        for w in sorted(glob.glob(str(self.WF / "*.yml"))):
            d = yaml.safe_load(open(w, encoding="utf-8")); on = d.get(True) or d.get("on") or {}
            if isinstance(on, str): on = {on: None}
            if isinstance(on, list): on = {k: None for k in on}
            if "push" not in on: continue
            pu = on["push"] or {}
            if pu.get("branches") and not any(pm(b, rama) for b in pu["branches"]): continue
            if pu.get("branches-ignore") and any(pm(b, rama) for b in pu["branches-ignore"]): continue
            if pu.get("paths") and not any(pm(p, f) for p in pu["paths"] for f in ficheros): continue
            disparan.append(Path(w).name)
        self.assertEqual(disparan, [], "un push de la rama de desarrollo dispararia: " + ", ".join(disparan))


if __name__ == "__main__":
    unittest.main()
