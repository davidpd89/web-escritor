"""Pruebas con git REAL (remoto bare local): el push solo toca mejoras-web/*; main y la rama base del remoto no se mueven; vista previa y worktree de lectura."""
import json, shutil, subprocess, unittest
from pathlib import Path
import util
import mw, actions, parches, preview
from types import SimpleNamespace as NS


class ConRemoto(util.Caso):
    def setUp(self):
        super().setUp()
        self.remoto = Path(self.tmp.name) / "remoto.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remoto)], check=True)
        util.git(self.repo, "remote", "add", "origin", str(self.remoto))
        util.git(self.repo, "push", "-q", "origin", "main:main", "main:lab/mejoras-web-20261024")
        util.git(self.repo, "fetch", "-q", "origin")  # ahora origin/lab/... es real
        self.main_remoto = util.git(self.remoto, "rev-parse", "main"); self.lab_remoto = util.git(self.remoto, "rev-parse", "lab/mejoras-web-20261024")
        actions.AUTORIZADO = True

    def test_push_real_solo_a_mejoras_web_y_main_no_se_mueve(self):
        self.exp_preparado(); ex = actions.Ejecutor(mw, gh=actions._SinGh(), cfg={"limite": None}); self.addCleanup(ex.c.close)
        ex.capturar(); it = self.c.execute("SELECT * FROM cola").fetchone(); self.assertEqual(it["estado"], "validado")
        gh = actions.Gh(mw); gh.push(it["sha"], it["rama"])
        self.assertEqual(util.git(self.remoto, "rev-parse", it["rama"]), it["sha"])
        self.assertEqual(gh.remote_sha(it["rama"]), it["sha"]); self.assertEqual(actions.Gh(mw).remotos(), {it["rama"]: it["sha"]})
        self.assertEqual(util.git(self.remoto, "rev-parse", "main"), self.main_remoto)  # main intacta
        self.assertEqual(util.git(self.remoto, "rev-parse", "lab/mejoras-web-20261024"), self.lab_remoto)  # y la rama base del laboratorio tambien
        for rama in ("main", "lab/mejoras-web-20261024"):
            with self.assertRaises(actions.GhAuthError): gh.push(it["sha"], rama)
        self.assertEqual(util.git(self.remoto, "rev-parse", "main"), self.main_remoto)
        # la rama del remoto solo contiene el commit del parche encima de la base
        self.assertEqual(util.git(self.remoto, "rev-list", "--count", f"lab/mejoras-web-20261024..{it['rama']}"), "1")

    def test_vista_previa_reconstruye_el_sha_y_limpia(self):
        self.exp_preparado(); ex = actions.Ejecutor(mw, gh=actions._SinGh(), cfg={"limite": None}); self.addCleanup(ex.c.close); ex.capturar()
        carpeta, wt = preview.raiz(mw, "MW-0001")
        try:
            self.assertIn('id="contenido"', (carpeta / "index.html").read_text(encoding="utf-8")); self.assertNotIn("contenido", (self.repo / "index.html").read_text(encoding="utf-8"))
            self.assertTrue(str(carpeta).startswith(str(mw.STATE)))
        finally: parches.limpiar_wt(wt)
        self.assertFalse(wt.exists())
        base, _ = preview.raiz(mw, None); self.assertNotIn("contenido", (base / "index.html").read_text(encoding="utf-8"))  # sin ID: la rama base tal cual
        with self.assertRaises(ValueError): preview.raiz(mw, "../etc")
        with self.assertRaises(ValueError): preview.raiz(mw, "MW-9999")

    def test_vista_previa_solo_en_localhost(self):
        src = (mw.HERE / "preview.py").read_text(encoding="utf-8"); self.assertIn('("127.0.0.1", a.puerto)', src); self.assertNotIn("0.0.0.0", src)


@unittest.skipUnless(shutil.which("node"), "node no instalado")
class TestsNode(util.Caso):
    def test_test_node_con_servidor_local_falla_en_la_base_y_pasa_con_el_cambio(self):
        test = ("import assert from 'node:assert/strict';\nconst res = await fetch(process.env.SITE_ORIGIN + '/index.html');\nconst html = await res.text();\n"
                "assert.ok(html.includes('id=\"contenido\"'), 'falta el id contenido en la portada');\nconsole.log('ok');\n")
        prop = self.propuesta_gpt(pruebas=[{"ruta": "tests/mejoras-web/mw-0001-skip.mjs", "contenido": test}])
        self.exp_preparado(prop=prop); ex = actions.Ejecutor(mw, gh=actions._SinGh(), cfg={"limite": None, "timeout_test_s": 60}); self.addCleanup(ex.c.close)
        ex.capturar(); it = self.c.execute("SELECT * FROM cola").fetchone()
        self.assertEqual(it["estado"], "validado", it["detalle"]); self.assertIn("demuestran la mejora", it["detalle"])
        self.assertEqual(self.c.execute("SELECT clase FROM cola_tests").fetchone()[0], "ok")

    def test_test_node_roto_se_detecta_antes_de_ejecutar(self):
        prop = self.propuesta_gpt(pruebas=[{"ruta": "tests/mejoras-web/mw-0001-skip.mjs", "contenido": "import assert from 'node:assert';\nassert.ok(true, 'x'); const = ;\n" + "// x" * 10}])
        self.exp_preparado(prop=prop); ex = actions.Ejecutor(mw, gh=actions._SinGh(), cfg={"limite": None}); self.addCleanup(ex.c.close); ex.capturar()
        self.assertEqual(self.c.execute("SELECT estado FROM cola").fetchone()[0], "fallo_local")


if __name__ == "__main__":
    unittest.main()
