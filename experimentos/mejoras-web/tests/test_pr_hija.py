import json, unittest
from types import SimpleNamespace as NS
import util
import mw, pr_hija, actions


class GhPrFalso:
    def __init__(self, previas=None, abiertas=None):
        self.previas, self.abiertas, self.creadas = previas or [], abiertas or [], []

    def de_rama(self, rama): return self.previas
    def abiertas_laboratorio(self): return self.abiertas

    def crear_borrador(self, rama, titulo, cuerpo):
        self.creadas.append((rama, titulo, cuerpo)); return "https://github.com/davidpd89/web-escritor/pull/901"


class Pr(util.Caso):
    def listo(self, estado="remoto_ok"):
        self.exp_preparado(estado=estado)
        sha = "a" * 40
        self.c.execute("UPDATE expedientes SET sha=?, base_sha=?, rama=?", (sha, "b" * 40, "mejoras-web/mw-0001"))
        self.c.execute("INSERT INTO cola(clave,exp,rama,sha,estado,tests,runs,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?)",
                       ("mejoras-web/mw-0001@aaaaaaaaaaaa", "MW-0001", "mejoras-web/mw-0001", sha, estado, "[]",
                        json.dumps({"1": {"id": 9, "url": "https://github.com/o/r/actions/runs/9", "conclusion": "success"}}), mw.now(), mw.now()))
        self.c.execute("INSERT INTO cola_tests VALUES(?,?,?,?,?,?,?)", ("mejoras-web/mw-0001@aaaaaaaaaaaa", "actions", "tests/mejoras-web/mw-0001-skip.py", "ok", 0, 9, mw.now())); self.c.commit()

    def a(self, **kw): return NS(id="MW-0001", confirmar=True, solo_local=False, **kw)

    def test_borrador_hacia_la_rama_de_laboratorio_con_cuerpo_completo(self):
        self.listo(); gh = GhPrFalso()
        self.assertEqual(pr_hija.main(mw, self.a(), gh), 0)
        rama, titulo, cuerpo = gh.creadas[0]
        self.assertEqual(rama, "mejoras-web/mw-0001"); self.assertIn("MW-0001", titulo)
        for s in ("## Necesidad", "## Cambio", "## Criterio de aceptacion", "https://github.com/o/r/actions/runs/9", "## Procedencia del codigo externo", "Revision de Claude", "no se fusiona", "BORRADOR"):
            self.assertIn(s.lower(), cuerpo.lower(), s)
        e = self.c.execute("SELECT * FROM expedientes").fetchone(); self.assertEqual((e["estado"], e["pr_url"]), ("pr_borrador", "https://github.com/davidpd89/web-escritor/pull/901"))

    def test_sin_confirmar_solo_simula(self):
        self.listo(); gh = GhPrFalso(); a = self.a(); a.confirmar = False
        self.assertEqual(pr_hija.main(mw, a, gh), 0); self.assertEqual(gh.creadas, [])
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "remoto_ok")

    def test_exige_validacion_remota_correcta(self):
        for estado in ("preparado", "validado", "remoto_fallo", "remoto_infra", "fallo_local", "en_actions"):
            self.c.execute("DELETE FROM expedientes"); self.c.execute("DELETE FROM cola"); self.c.execute("DELETE FROM cola_tests"); self.c.commit()
            self.listo(estado=estado); gh = GhPrFalso()
            self.assertEqual(pr_hija.main(mw, self.a(), gh), 2, estado); self.assertEqual(gh.creadas, [])

    def test_solo_local_permite_validado_sin_actions(self):
        self.listo(estado="validado"); self.c.execute("UPDATE cola SET runs='{}'"); self.c.commit(); gh = GhPrFalso(); a = self.a(); a.solo_local = True
        actions.Gh.push = lambda self, sha, rama: None  # no hay remoto en la prueba
        try: self.assertEqual(pr_hija.main(mw, a, gh), 0)
        finally: del actions.Gh.push
        self.assertIn("No se ejecuto en Actions", gh.creadas[0][2]); self.assertFalse(actions.AUTORIZADO)

    def test_no_duplica_si_ya_hay_pr_abierta_para_la_rama(self):
        self.listo(); gh = GhPrFalso(previas=[{"number": 5, "url": "https://github.com/o/r/pull/5", "state": "OPEN"}])
        self.assertEqual(pr_hija.main(mw, self.a(), gh), 0); self.assertEqual(gh.creadas, [])
        self.assertEqual(self.c.execute("SELECT pr_url FROM expedientes").fetchone()[0], "https://github.com/o/r/pull/5")

    def test_tope_de_prs_hijas_abiertas(self):
        self.listo(); gh = GhPrFalso(abiertas=[{"number": 1}, {"number": 2}])
        self.assertEqual(pr_hija.main(mw, self.a(), gh), 2); self.assertEqual(gh.creadas, [])

    def test_nunca_a_main_ni_a_ramas_ajenas(self):
        ordenes = []
        g = pr_hija.GhPr(mw, ejecutar=lambda args: ordenes.append(args) or "https://github.com/o/r/pull/1")
        for rama in ("main", "gpt-qa/x", "lab/mejoras-web-20261024"):
            with self.assertRaises(pr_hija.PrError): g.crear_borrador(rama, "t", "c")
        mw.CFG["rama_base"] = "main"
        with self.assertRaises(pr_hija.PrError): g.crear_borrador("mejoras-web/mw-1", "t", "c")
        mw.CFG["rama_base"] = "lab/mejoras-web-20261024"
        self.assertEqual(ordenes, [])
        g.crear_borrador("mejoras-web/mw-1", "t", "c"); a = ordenes[0]
        self.assertIn("--draft", a); self.assertEqual(a[a.index("--base") + 1], "lab/mejoras-web-20261024"); self.assertNotIn("main", a)

    def test_la_cola_debe_contener_el_sha_actual(self):
        self.listo(); self.c.execute("UPDATE expedientes SET sha=?", ("c" * 40,)); self.c.commit()
        self.assertEqual(pr_hija.main(mw, self.a(), GhPrFalso()), 2)

    def test_sin_metodos_de_fusion(self):
        for m in ("merge", "pr_merge", "auto_merge", "cerrar", "close"): self.assertFalse(hasattr(pr_hija.GhPr, m), m)


if __name__ == "__main__":
    unittest.main()
