import json, os, shutil, subprocess, sys, threading, unittest, urllib.request
from pathlib import Path
from unittest import mock
import util
import mw, vista_publica as V

BUILD = """import argparse, shutil, sys
from pathlib import Path
p = argparse.ArgumentParser(); p.add_argument('--out'); p.add_argument('--check-contents', action='store_true'); a = p.parse_args()
if a.check_contents:
    assert (Path(a.out) / 'index.html').is_file(); sys.exit(0)
out = Path(a.out); out.mkdir(parents=True); (out / 'index.html').write_text(Path('index.html').read_text(encoding='utf-8') + Path('version.txt').read_text(encoding='utf-8'), encoding='utf-8'); (out / 'robots.txt').write_text('User-agent: *\\nAllow: /\\n')
"""


class Caso(util.Caso):
    def setUp(self):
        super().setUp()
        (self.repo / "scripts").mkdir(); (self.repo / "scripts" / "build-public-dist.py").write_text(BUILD, encoding="utf-8")
        (self.repo / "version.txt").write_text("base v1", encoding="utf-8")
        util.git(self.repo, "add", "-A"); util.git(self.repo, "commit", "-qm", "build"); self.avanzar_lab()
        self.v = V.Vista(mw)

    def avanzar_lab(self): util.git(self.repo, "update-ref", "refs/remotes/origin/lab/mejoras-web-20261024", "HEAD")

    def publicar_texto(self, texto):
        (self.repo / "version.txt").write_text(texto, encoding="utf-8"); util.git(self.repo, "commit", "-qam", texto); self.avanzar_lab()


class Construccion(Caso):
    def test_construye_el_artefacto_publico_con_noindex_y_pagina_de_cambios(self):
        self.exp_preparado("MW-0001", estado="integrado")
        self.c.execute("UPDATE expedientes SET titulo='Mejora <b>x</b> & y'"); self.c.commit()
        self.assertTrue(self.v.refrescar(self.c))
        self.assertIn("base v1", (self.v.actual / "index.html").read_text(encoding="utf-8"))
        self.assertEqual((self.v.actual / "robots.txt").read_text(), "User-agent: *\nDisallow: /\n")  # la vista previa no se indexa
        p = (self.v.actual / "_lab" / "index.html").read_text(encoding="utf-8")
        self.assertIn("MW-0001", p); self.assertIn("Mejora &lt;b&gt;x&lt;/b&gt; &amp; y", p); self.assertNotIn("<b>x</b>", p)  # contenido escapado
        self.assertIn("noindex", p); self.assertEqual(json.loads((self.v.dir / "vista.json").read_text())["sha"], util.git(self.repo, "rev-parse", "HEAD"))

    def test_solo_lista_integradas_y_con_pr(self):
        self.exp_preparado("MW-0001", estado="integrado"); self.exp_preparado("MW-0002", estado="descartado_claude"); self.exp_preparado("MW-0003", estado="preparado")
        self.v.refrescar(self.c); p = (self.v.actual / "_lab" / "index.html").read_text(encoding="utf-8")
        self.assertIn("MW-0001", p); self.assertNotIn("MW-0002", p); self.assertNotIn("MW-0003", p)

    def test_no_reconstruye_si_lab_no_cambio_y_si_cambia(self):
        self.assertTrue(self.v.refrescar(self.c)); self.assertFalse(self.v.refrescar(self.c))
        self.publicar_texto("base v2"); self.assertTrue(self.v.refrescar(self.c)); self.assertIn("base v2", (self.v.actual / "index.html").read_text(encoding="utf-8"))

    def test_un_build_roto_conserva_el_sitio_anterior(self):
        self.v.refrescar(self.c)
        (self.repo / "scripts" / "build-public-dist.py").write_text("import sys; sys.exit(3)", encoding="utf-8"); util.git(self.repo, "commit", "-qam", "roto"); self.avanzar_lab()
        with self.assertRaises(RuntimeError): self.v.refrescar(self.c)
        self.assertIn("base v1", (self.v.actual / "index.html").read_text(encoding="utf-8"))  # sigue sirviendo lo ultimo bueno

    def test_sirve_solo_lo_construido_y_con_cabeceras_noindex(self):
        self.v.refrescar(self.c); srv, _ = V.servir(self.v, 0); self.addCleanup(srv.shutdown); puerto = srv.server_address[1]
        r = urllib.request.urlopen(f"http://127.0.0.1:{puerto}/"); self.assertIn(b"base v1", r.read()); self.assertIn("noindex", r.headers["X-Robots-Tag"])
        with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(f"http://127.0.0.1:{puerto}/scripts/build-public-dist.py")  # nada interno
        self.assertEqual(srv.server_address[0], "127.0.0.1")
        self.publicar_texto("base v3"); self.v.refrescar(self.c)  # el servidor sigue y sirve la version nueva sin reiniciarse
        self.assertIn(b"base v3", urllib.request.urlopen(f"http://127.0.0.1:{puerto}/").read())


class Tunel(Caso):
    def test_extrae_url_de_cloudflared_y_localhost_run(self):
        self.assertEqual(V.extraer_url("2026 INF |  https://rapid-cat-1234.trycloudflare.com  |"), "https://rapid-cat-1234.trycloudflare.com")
        self.assertEqual(V.extraer_url("abc123.lhr.life tunneled with tls termination, https://abc123.lhr.life"), "https://abc123.lhr.life")
        self.assertIsNone(V.extraer_url("Connection established")); self.assertIsNone(V.extraer_url("https://evil.example.com/x"))

    def test_prefiere_cloudflared_y_cae_a_ssh(self):
        self.assertEqual(V.comando_tunel(8780, lambda n: "/x/cloudflared" if n == "cloudflared" else "/x/ssh")[0], "cloudflared")
        nombre, args = V.comando_tunel(8780, lambda n: "/x/ssh" if n == "ssh" else None)
        self.assertEqual(nombre, "localhost.run"); self.assertIn("80:127.0.0.1:8780", args); self.assertIn("BatchMode=yes", args)
        self.assertIsNone(V.comando_tunel(8780, lambda n: None))

    def test_el_tunel_escribe_la_url_y_se_relanza_si_cae(self):
        class P:
            def __init__(s, lineas): s.stdout = iter(lineas); s.cod = None
            def poll(s): return s.cod
            def terminate(s): s.cod = 0
        lanzados = []
        def popen(args, **k): p = P(["conectando\n", "https://aaa-bbb.trycloudflare.com\n"]); lanzados.append(p); return p
        t = V.Tunel(self.v, 8780, popen=popen, which=lambda n: "/x/cloudflared" if n == "cloudflared" else None)
        self.assertTrue(t.asegurar()); import time; time.sleep(0.2)
        self.assertEqual(json.loads((self.v.dir / "vista.json").read_text())["url"], "https://aaa-bbb.trycloudflare.com")
        t.asegurar(); self.assertEqual(len(lanzados), 1)  # vivo: no relanza
        lanzados[0].cod = 1; t.asegurar(); self.assertEqual(len(lanzados), 2)  # cayo: lo relanza

    def test_sin_ningun_cliente_lo_dice(self):
        V.Tunel(self.v, 8780, which=lambda n: None).asegurar(); self.assertIn("instala cloudflared", json.loads((self.v.dir / "vista.json").read_text())["tunel"])


class Bucle(Caso):
    def test_un_ciclo_construye_sirve_y_lanza_el_tunel(self):
        mw.CFG["vista_publica"] = {"puerto": 0, "refresco_s": 1}; lanzado = []
        class P:
            stdout = iter([]); 
            def poll(s): return None
            def terminate(s): pass
        with mock.patch.object(V, "servir", lambda v, p: (mock.Mock(), None)), mock.patch.object(V.shutil, "which", lambda n: "/x/cloudflared" if n == "cloudflared" else None):
            V.bucle(mw, vista=self.v, popen=lambda a, **k: lanzado.append(a) or P(), una_vez=True)
        self.assertTrue((self.v.actual / "index.html").is_file()); self.assertEqual(len(lanzado), 1)
        self.assertFalse(mw.Lock("vista").path.exists())  # libera su bloqueo

    def test_no_arranca_dos_a_la_vez(self):
        mw.STATE.mkdir(parents=True, exist_ok=True); mw.Lock("vista").path.write_text(f"{os.getppid()} {mw.now()}")
        with self.assertRaises(SystemExit) as cm: V.bucle(mw, vista=self.v, una_vez=True)
        self.assertEqual(cm.exception.code, mw.RC_EN_MARCHA)

    def test_estado_muestra_la_url_y_la_pagina_de_cambios(self):
        import informe
        self.v.escribir(url="https://aaa.trycloudflare.com", sha="a" * 40, local="http://127.0.0.1:8780/")
        with mock.patch.object(mw.Lock, "dueno", lambda self_: 4242 if self_.nombre == "vista" else 0):
            t = informe.texto(mw)
        self.assertIn("https://aaa.trycloudflare.com", t); self.assertIn("/_lab/", t); self.assertIn("VISTA PREVIA (temporal, no es main)", t)

    def test_no_toca_main_ni_pages_ni_cloudflare(self):
        src = (mw.HERE / "vista_publica.py").read_text(encoding="utf-8")
        import re; codigo = re.sub(r'"""[\s\S]*?"""', "", src).lower()
        for malo in ("push", "origin main", "wrangler", "workflow", "merge"): self.assertNotIn(malo, codigo, malo)



if __name__ == "__main__":
    unittest.main()
