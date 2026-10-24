import json, subprocess, sys, tempfile, unittest
from pathlib import Path

DRV = Path(__file__).resolve().parent / "ci_grupo.py"


def correr(cwd, modo, *args):
    out = Path(cwd) / "res.json"
    r = subprocess.run([sys.executable, str(DRV), str(out), modo, *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, (json.loads(out.read_text(encoding="utf-8")) if out.exists() else None)


class CiGrupo(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.p = Path(self.d.name)
    def tearDown(self): self.d.cleanup()

    def test_sin_entorno_falla_el_grupo(self):
        (self.p / "a.mjs").write_text("import 'playwright-no-existe'\n"); (self.p / "p.mjs").write_text("import 'playwright'\n")
        rc, r = correr(self.p, "exploratorio", "node:p.mjs")
        self.assertEqual(rc, 1); self.assertEqual(r["resumen"], {"sin_entorno": 1})

    def test_hallazgo_exploratorio_no_falla_pero_regresion_si(self):
        (self.p / "t.py").write_text("raise AssertionError('x')\n")
        self.assertEqual(correr(self.p, "exploratorio", "python:t.py")[0], 0)
        self.assertEqual(correr(self.p, "regresion", "python:t.py")[0], 1)

    def test_argumentos_invalidos_no_ejecutan_nada(self):
        (self.p / "t.py").write_text("open('marca','w')\n")
        for mal in ("python:../t.py", "python:/etc/x.py", "bash:t.py", "python:t.py;touch", "python:t.txt"):
            rc, r = correr(self.p, "exploratorio", "python:t.py", mal)
            self.assertEqual(rc, 2, mal); self.assertFalse((self.p / "marca").exists())
        self.assertEqual(correr(self.p, "otro", "python:t.py")[0], 2)

    def test_un_solo_argumento_con_varios_tests(self):
        for n in ("a.py", "b.py"): (self.p / n).write_text("print(1)\n")
        rc, r = correr(self.p, "exploratorio", "python:a.py python:b.py")
        self.assertEqual((rc, r["resumen"]), (0, {"ok": 2}))

    def test_timeout_es_infra(self):
        (self.p / "t.py").write_text("import time; time.sleep(30)\n")
        out = self.p / "res.json"
        subprocess.run([sys.executable, str(DRV), str(out), "exploratorio", "python:t.py"], cwd=self.p, env={**__import__("os").environ, "QA_TEST_TIMEOUT": "2"})
        self.assertEqual(json.loads(out.read_text())["resumen"], {"infra": 1})


if __name__ == "__main__": unittest.main()
