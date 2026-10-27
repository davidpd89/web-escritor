import base64, json, unittest
from pathlib import Path
import util
import mw, parches, verificar_upstream


class Rutas(unittest.TestCase):
    def test_rutas_prohibidas(self):
        for r in (".github/workflows/x.yml", "package.json", "scripts/qa-gpt/qa_gpt.py", "experimentos/mejoras-web/motor/mw.py", "/etc/passwd", "../x", "a//b",
                  "cloudflare-worker-subscribe.js", "data/stripe.json", ".env", "C:\\x"):
            self.assertTrue(parches.ruta_segura(r), r)
        for r in ("index.html", "assets/app.js", "tests/mejoras-web/a.py"): self.assertIsNone(parches.ruta_segura(r), r)


class Parche(unittest.TestCase):
    TXT = {"index.html": "<a>uno</a>\n<b>dos</b>\n<b>dos</b>\n"}
    leer = staticmethod(lambda r: Parche.TXT.get(r))

    def v(self, p): return parches.validar_parche(p, self.leer)

    def test_valido(self):
        ok, pr, n = self.v({"ficheros": [{"ruta": "index.html", "reemplazos": [{"buscar": "<a>uno</a>", "por": "<a>UNO</a>"}]}]})
        self.assertTrue(ok, pr)

    def test_buscar_debe_ser_unico(self):
        ok, pr, _ = self.v({"ficheros": [{"ruta": "index.html", "reemplazos": [{"buscar": "<b>dos</b>", "por": "x"}]}]})
        self.assertFalse(ok); self.assertIn("2 veces", pr[0])
        ok, pr, _ = self.v({"ficheros": [{"ruta": "index.html", "reemplazos": [{"buscar": "<i>", "por": "x"}]}]})
        self.assertIn("0 veces", pr[0])

    def test_secreto_ruta_y_inexistente(self):
        ok, pr, _ = self.v({"ficheros": [{"ruta": "index.html", "reemplazos": [{"buscar": "<a>uno</a>", "por": "token = 'abcdefghijkl'"}]}]})
        self.assertFalse(ok)
        self.assertFalse(self.v({"ficheros": [{"ruta": ".github/workflows/a.yml", "reemplazos": [{"buscar": "a", "por": "b"}]}]})[0])
        self.assertIn("no existe", self.v({"ficheros": [{"ruta": "nuevo.html", "reemplazos": [{"buscar": "a", "por": "b"}]}]})[1][0])

    def test_ficheros_nuevos(self):
        ok, pr, n = self.v({"ficheros_nuevos": [{"ruta": "assets/skip.css", "contenido": ".skip{top:0}"}]}); self.assertTrue(ok, pr)
        self.assertIn("ya existe", self.v({"ficheros_nuevos": [{"ruta": "index.html", "contenido": "x"}]})[1][0])
        self.assertIn("extension", self.v({"ficheros_nuevos": [{"ruta": "assets/x.exe", "contenido": "x"}]})[1][0])
        self.assertFalse(self.v({"ficheros_nuevos": [{"ruta": "assets/big.css", "contenido": "a" * 70000}]})[0])
        self.assertIn("pruebas", self.v({"ficheros_nuevos": [{"ruta": "tests/mejoras-web/t.py", "contenido": "x"}]})[1][0])

    def test_limites(self):
        self.assertFalse(self.v({"ficheros": []})[0]); self.assertFalse(self.v("no")[0])
        mw.CFG["parches"]["max_ficheros_nuevos"] = 1
        try: self.assertFalse(self.v({"ficheros_nuevos": [{"ruta": "a.css", "contenido": "x"}, {"ruta": "b.css", "contenido": "y"}]})[0])
        finally: mw.CFG["parches"]["max_ficheros_nuevos"] = 4


class Pruebas(unittest.TestCase):
    T = "import sys\nhtml = open('index.html').read()\nassert 'skip' in html, 'falta'\n"

    def test_valida_y_rechazos(self):
        ok, pr, n = parches.validar_pruebas([{"ruta": "tests/mejoras-web/a.py", "contenido": self.T}]); self.assertTrue(ok, pr); self.assertEqual(n[0]["exe"], "python")
        self.assertFalse(parches.validar_pruebas([])[0])
        self.assertFalse(parches.validar_pruebas([{"ruta": "tests/otro/a.py", "contenido": self.T}])[0])  # fuera del directorio de tests de mejoras
        self.assertFalse(parches.validar_pruebas([{"ruta": "tests/mejoras-web/a.py", "contenido": "print('hola mundo, sin comprobar nada en absoluto')\n"}])[0])
        self.assertFalse(parches.validar_pruebas([{"ruta": "tests/mejoras-web/a.py", "contenido": "def x(:\n    assert True  # " + "x" * 40}])[0])  # sintaxis
        self.assertTrue(parches.validar_pruebas([{"ruta": "tests/mejoras-web/a.mjs", "contenido": "import assert from 'node:assert'; assert.ok(true, 'x'); // " + "x" * 30}])[0])


class PruebasPeligrosas(unittest.TestCase):
    OK = "assert 'skip' in open('index.html', encoding='utf-8').read(), 'falta'\n"

    def v(self, ruta, cont): return parches.validar_pruebas([{"ruta": ruta, "contenido": cont}])

    def test_rechaza_operaciones_peligrosas_en_python(self):
        for malo in ("import subprocess\nsubprocess.run(['rm','-rf','x'])\nassert True\n", "import os\nos.system('calc')\nassert True\n", "import shutil\nshutil.rmtree('x')\nassert True\n",
                     "import urllib.request\nassert urllib.request.urlopen('http://x')\n", "exec('1')\nassert True\n", "open('f.txt', 'w').write('x')\nassert True\n",
                     "import socket\nassert socket\n", "__import__('os').remove('x')\nassert True\n"):
            ok, pr, _ = self.v("tests/mejoras-web/a.py", malo + "# relleno de longitud para pasar el minimo\n"); self.assertFalse(ok, malo); self.assertIn("no permitida", pr[0])
        self.assertTrue(self.v("tests/mejoras-web/a.py", self.OK + "# relleno de longitud\n")[0])
        self.assertTrue(self.v("tests/mejoras-web/a.py", "import re, json\nhtml = open('index.html', encoding='utf-8').read()\nassert re.search('x', html), 'm'\n")[0])

    def test_rechaza_operaciones_peligrosas_en_node_y_admite_playwright_y_fetch_local(self):
        for malo in ("import { execSync } from 'node:child_process';\nassert.ok(1, 'x');", "import fs from 'node:fs';\nfs.writeFileSync('a','b'); assert.ok(1,'x');", "eval('1'); assert.ok(1, 'x');",
                     "import http from 'node:http';\nassert.ok(http, 'x');", "fs.rmSync('x'); assert.ok(1, 'x');"):
            self.assertFalse(self.v("tests/mejoras-web/a.mjs", malo + "\n// relleno de longitud para pasar el minimo\n")[0], malo)
        bueno = ("import assert from 'node:assert/strict';\nimport { chromium } from 'playwright';\nimport fs from 'node:fs';\nconst b = await chromium.launch();\n"
                 "const html = fs.readFileSync('index.html', 'utf8');\nconst r = await fetch(process.env.SITE_ORIGIN + '/');\nassert.ok(html.includes('x') && r.ok, 'm');\nawait b.close();\n")
        ok, pr, _ = self.v("tests/mejoras-web/a.mjs", bueno); self.assertTrue(ok, pr)


class Procedencia(unittest.TestCase):
    SHA, COMMIT = "a" * 40, "c" * 40
    LIT = "function skipLink() {\n  return document.querySelector('#contenido');\n}"

    def fetch(self, url):
        if "/contents/src/skip.js?" in url: return {"type": "file", "sha": self.SHA}
        if "/git/blobs/" in url: return {"sha": self.SHA, "encoding": "base64", "content": base64.b64encode((self.LIT + "\n").encode()).decode()}
        if url.endswith("/license"): return {"license": {"spdx_id": "MIT"}}
        raise AssertionError(url)

    def ext(self, **kw):
        e = {"url": "https://github.com/org/skip", "commit_upstream": self.COMMIT, "ruta_upstream": "src/skip.js", "fuente_sha": self.SHA, "codigo_original": self.LIT, "licencia": "MIT"}
        e.update(kw); return e

    def test_verificado_con_literal_en_el_parche(self):
        ok, pr, regs = parches.verificar_procedencia([self.ext()], ["// de org/skip\n" + self.LIT], self.fetch)
        self.assertTrue(ok, pr); self.assertEqual(regs[0]["licencia"], "MIT"); self.assertEqual(regs[0]["commit"], self.COMMIT); self.assertEqual(regs[0]["ruta"], "src/skip.js")

    def test_literal_ausente_del_parche_se_rechaza_salvo_adaptacion_declarada(self):
        ok, pr, _ = parches.verificar_procedencia([self.ext()], ["codigo distinto"], self.fetch); self.assertFalse(ok); self.assertIn("literal", pr[0])
        ok, pr, regs = parches.verificar_procedencia([self.ext(adaptado=True, adaptacion="Renombrado a #contenido y sin dependencias")], ["codigo distinto"], self.fetch)
        self.assertTrue(ok, pr); self.assertTrue(regs[0]["adaptado"])

    def test_licencia_distinta_commit_ausente_o_blob_falso(self):
        self.assertFalse(parches.verificar_procedencia([self.ext(licencia="GPL-3.0")], [self.LIT], self.fetch)[0])
        self.assertFalse(parches.verificar_procedencia([self.ext(commit_upstream="")], [self.LIT], self.fetch)[0])
        self.assertFalse(parches.verificar_procedencia([self.ext(fuente_sha="b" * 40)], [self.LIT], self.fetch)[0])
        self.assertFalse(parches.verificar_procedencia([self.ext(url="https://ejemplo.org/doc")], [self.LIT], self.fetch)[0])  # no es un repo: no vale como "codigo original"

    def test_sin_codigo_externo_es_valido(self):
        self.assertEqual(parches.verificar_procedencia([], ["x"], self.fetch)[:2], (True, []))


class Candidata(util.Caso):
    def test_construir_aplica_y_commitea_en_worktree_separado(self):
        eid = self.exp_preparado()
        e = self.c.execute("SELECT * FROM expedientes WHERE id=?", (eid,)).fetchone()
        wt, sha, base, tocados = parches.construir_candidata(e)
        try:
            self.assertEqual(sorted(tocados), ["index.html", "tests/mejoras-web/mw-0001-skip.py"])
            self.assertIn('href="#contenido"', (wt / "index.html").read_text(encoding="utf-8"))
            self.assertEqual(util.git(self.repo, "rev-parse", "mejoras-web/mw-0001"), sha)  # rama LOCAL; no hay remoto ni push
            self.assertNotEqual(sha, base)
            self.assertEqual(util.git(self.repo, "rev-parse", "origin/lab/mejoras-web-20261024"), base)  # la base no se mueve
            self.assertNotIn("skip", (self.repo / "index.html").read_text(encoding="utf-8"))  # el checkout de David no se toca
        finally: parches.limpiar_wt(wt)

    def test_parche_que_no_encaja_no_deja_rama_ni_worktree(self):
        eid = self.exp_preparado()
        self.c.execute("UPDATE expedientes SET parche=? WHERE id=?", (json.dumps({"parche": {"ficheros": [{"ruta": "index.html", "reemplazos": [{"buscar": "NO EXISTE", "por": "x"}]}], "ficheros_nuevos": []}, "pruebas": [], "tocados": []}), eid))
        e = self.c.execute("SELECT * FROM expedientes WHERE id=?", (eid,)).fetchone()
        with self.assertRaises(ValueError): parches.construir_candidata(e)
        self.assertEqual(util.git(self.repo, "branch", "--list", "mejoras-web/*"), "")
        self.assertFalse(parches.wt_path(eid).exists())

    def test_fichero_con_crlf_no_se_convierte_a_lf(self):
        (self.repo / "index.html").write_bytes(util.HTML.replace("\n", "\r\n").encode()); util.git(self.repo, "commit", "-qam", "crlf")
        util.git(self.repo, "update-ref", "refs/remotes/origin/lab/mejoras-web-20261024", "HEAD")
        e = self.c.execute("SELECT * FROM expedientes WHERE id=?", (self.exp_preparado(),)).fetchone()
        with self.assertRaisesRegex(ValueError, "CRLF"): parches.construir_candidata(e)
        self.assertEqual(util.git(self.repo, "branch", "--list", "mejoras-web/*"), "")

    def test_rama_ajena_rechazada(self):
        eid = self.exp_preparado()
        self.c.execute("UPDATE expedientes SET rama='gpt-qa/robo' WHERE id=?", (eid,))
        with self.assertRaises(ValueError): parches.construir_candidata(self.c.execute("SELECT * FROM expedientes WHERE id=?", (eid,)).fetchone())


if __name__ == "__main__":
    unittest.main()


class PeligroEnTextoNoEsPeligro(unittest.TestCase):
    def test_palabra_en_comentario_o_cadena_no_cuenta_pero_el_import_si(self):
        nl = chr(10)
        self.assertIsNone(parches.peligro_python(nl.join(['"""usa importlib"""', "# eval", 'x = "exec("', "assert x", ""])))
        self.assertEqual(parches.peligro_python(nl.join(["import importlib.util", "assert 1", ""])), "importlib")
