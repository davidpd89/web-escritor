import json, sqlite3, unittest

import qa_campanas
import qa_gpt as q
import qa_triaje


class Campanas(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(":memory:"); self.c.row_factory = sqlite3.Row
        qa_triaje.migrar(self.c)
        self.c.executescript("""CREATE TABLE propuestas(id INTEGER PRIMARY KEY, huella TEXT UNIQUE, area TEXT, titulo TEXT, datos TEXT, estado TEXT, creado TEXT, actualizado TEXT, tecnica TEXT, funcionalidad TEXT);
            CREATE TABLE hallazgos(clave TEXT PRIMARY KEY, tipo TEXT, contrato TEXT, causa TEXT, familia TEXT, paginas INTEGER, urls TEXT, ejemplos TEXT, estado TEXT, nota TEXT, evidencia TEXT);""")
        self.c.execute("INSERT INTO hallazgos VALUES('h1','navegador','ux-objetivos-tactiles','objetivos tactiles < 24px','libros',2,?,?, 'a_triar',NULL,'ev')", (json.dumps(["/a/", "/b/"]), json.dumps(["/a/ 3 elementos"])))
        self.c.execute("INSERT INTO hallazgos VALUES('h2','estatico','seo-description','meta description corta','autores',1,?,'[]','a_triar',NULL,'ev')", (json.dumps(["https://x.com/autores/dk/"]),))
        self.c.execute("INSERT INTO hallazgos VALUES('h3','estatico','contrato-sin-plantilla','x','y',1,'[\"/z/\"]','[]','a_triar',NULL,'ev')")
        self.c.commit()

    def test_siembra_causas_aprobadas_con_test_y_es_idempotente(self):
        self.assertEqual(qa_campanas.sembrar(q, self.c, out=lambda *a: None), 2)
        self.assertEqual(qa_campanas.sembrar(q, self.c, out=lambda *a: None), 0)
        filas = self.c.execute("SELECT * FROM triaje ORDER BY id").fetchall()
        self.assertEqual([(r["decision"], r["prioridad"], r["clase"]) for r in filas], [("corregir", "1", "defecto_web")] * 2)
        rutas = [json.loads(r["datos"])["ficheros_nuevos"][0]["ruta"] for r in self.c.execute("SELECT datos FROM propuestas ORDER BY id")]
        self.assertEqual(rutas, ["qa/campana-tactiles-libros.mjs", "tests/test-campana-meta-description-autores.py"])
        py = json.loads(self.c.execute("SELECT datos FROM propuestas WHERE id=2").fetchone()[0])["ficheros_nuevos"][0]["contenido"]
        compile(py, "t.py", "exec"); self.assertIn('"autores/dk/index.html"', py)
        self.assertEqual(self.c.execute("SELECT estado FROM hallazgos WHERE clave='h3'").fetchone()[0], "a_triar")  # sin plantilla: no se toca


class PlantillasEstaticas(unittest.TestCase):
    def _correr(self, contrato, paginas, urls, extra=None):
        import pathlib, subprocess, sys, tempfile
        h = {"contrato": contrato, "familia": "fam"}
        ruta, py, _ = qa_campanas.PLANTILLAS[contrato](h, urls)
        compile(py, ruta, "exec")
        with tempfile.TemporaryDirectory() as d:
            raiz = pathlib.Path(d)
            for rel, txt in {**paginas, **(extra or {})}.items():
                (raiz / rel).parent.mkdir(parents=True, exist_ok=True); (raiz / rel).write_text(txt, encoding="utf-8")
            (raiz / "tests").mkdir(exist_ok=True); (raiz / ruta).write_text(py, encoding="utf-8")
            return subprocess.run([sys.executable, str(raiz / ruta)], capture_output=True, text=True).returncode

    def test_axe_enlaces_jsonld_y_sitemap_distinguen_bien_de_mal(self):
        ok = '<html lang="es"><h1>t</h1><img src="a.png" alt="x"><a href="/b/">b</a><script type="application/ld+json">{"@context":"https://schema.org","@type":"Thing"}</script></html>'
        mal = '<html><img src="a.png"><a href="/nada/">n</a><script type="application/ld+json">{</script></html>'
        extra = {"b/index.html": "<html></html>", "sitemap.xml": "<urlset>/a/</urlset>"}
        for c in ("a11y-imagenes", "navegacion-enlaces", "datos-jsonld"):
            self.assertEqual(self._correr(c, {"a/index.html": ok}, ["/a/"], extra), 0, c)
            self.assertEqual(self._correr(c, {"a/index.html": mal}, ["/a/"], extra), 1, c)
        self.assertEqual(self._correr("seo-sitemap", {}, ["/a/"], extra), 0)
        self.assertEqual(self._correr("seo-sitemap", {}, ["/z/"], extra), 1)
