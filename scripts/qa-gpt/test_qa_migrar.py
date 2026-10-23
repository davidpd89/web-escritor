"""Pruebas de qa_migrar (migracion de estado.db) y qa_coste (tabla de coste de Actions)."""
import json, sqlite3, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_gpt as q, qa_migrar as M, qa_coste as C


def datos(ruta, como="python tests/t.py"):
    return {"titulo": "t", "categoria": "regresion", "ficheros_nuevos": [{"ruta": ruta, "contenido": "print(1)"}], "como_ejecutar": como}


class Migrar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True); t = Path(self.tmp.name)
        q.STATE = t / "state"; q.DB_PATH = q.STATE / "e.db"; q.Lock.path = q.STATE / "worker.lock"
        self.c = q.db(); self.t = t
        for i, est in enumerate(("preparada", "aprobada", "ejecutada", "publicada"), 1):
            self.c.execute("INSERT INTO propuestas(id,huella,area,titulo,datos,estado,creado,actualizado) VALUES(?,?,?,?,?,?,?,?)",
                           (i, f"h{i}", "z", f"p{i}", json.dumps(datos("tests/t.py")), est, q.now(), q.now()))
        self.c.commit(); self.c.close()

    def tearDown(self): self.tmp.cleanup()

    def leer(self):
        c = sqlite3.connect(q.DB_PATH); c.row_factory = sqlite3.Row
        r = {x["id"]: (x["estado"], json.loads(x["datos"])) for x in c.execute("SELECT id,estado,datos FROM propuestas")}
        ev = c.execute("SELECT COUNT(*) FROM eventos WHERE estado='migrada_pasos'").fetchone()[0]; c.close(); return r, ev

    def test_ensayo_no_escribe_nada(self):
        antes = self.leer(); r = M.migrar(q.DB_PATH, self.t / "bk", "2026-10-23T10:00:00", aplicar=False)
        self.assertTrue(r["ok"]); self.assertEqual(r["migradas"], [1, 2]); self.assertEqual(self.leer(), antes); self.assertFalse((self.t / "bk").exists())

    def test_migra_solo_lo_pendiente_con_copia_y_sin_tocar_ejecutadas(self):
        antes, _ = self.leer(); r = M.migrar(q.DB_PATH, self.t / "bk", "2026-10-23T10:00:00")
        self.assertTrue(r["ok"], r); self.assertEqual(r["migradas"], [1, 2]); self.assertTrue(Path(r["backup"]).exists())
        desp, ev = self.leer(); self.assertEqual(ev, 2)
        for i in (3, 4): self.assertEqual(desp[i], antes[i])  # ejecutada / publicada intactas
        for i in (1, 2): self.assertIn("pasos", desp[i][1]); self.assertEqual(desp[i][0], antes[i][0])  # estado conservado
        self.assertEqual({k: v[0] for k, v in desp.items()}, {k: v[0] for k, v in antes.items()})  # contadores por estado
        b = sqlite3.connect(r["backup"]); self.assertEqual(b.execute("SELECT COUNT(*) FROM propuestas").fetchone()[0], 4); b.close()

    def test_idempotente_no_duplica_eventos(self):
        M.migrar(q.DB_PATH, self.t / "bk", "2026-10-23T10:00:00"); r2 = M.migrar(q.DB_PATH, self.t / "bk", "2026-10-23T11:00:00")
        self.assertTrue(r2["ok"]); self.assertEqual(r2["migradas"], []); self.assertIsNone(r2["backup"]); self.assertEqual(self.leer()[1], 2)

    def test_rollback_si_falla_a_mitad(self):
        antes = self.leer(); orig = M.cob.normalizar_comandos; n = []
        def roto(d):
            n.append(1)
            if len(n) == 2: raise RuntimeError("fallo simulado")
            return orig(d)
        M.cob.normalizar_comandos = roto
        try: r = M.migrar(q.DB_PATH, self.t / "bk", "2026-10-23T10:00:00")
        finally: M.cob.normalizar_comandos = orig
        self.assertFalse(r["ok"]); self.assertEqual(self.leer(), antes); self.assertTrue(Path(r["backup"]).exists())

    def test_esquema_incompatible_se_rechaza_sin_tocar(self):
        p = self.t / "raro.db"; c = sqlite3.connect(p); c.execute("CREATE TABLE propuestas(id INTEGER)"); c.commit(); c.close()
        r = M.migrar(p, self.t / "bk", "2026-10-23T10:00:00"); self.assertFalse(r["ok"]); self.assertIn("esquema", r["error"])


class Coste(unittest.TestCase):
    WF = "on:\n  workflow_dispatch:\njobs:\n  uno:\n    runs-on: x\n  dos-b:\n    runs-on: x\n# fin\n"

    def test_jobs_de(self): self.assertEqual(C.jobs_de(self.WF), ["uno", "dos-b"]); self.assertEqual(C.jobs_de("on: x\n"), [])

    def test_tabla_distingue_estados_y_no_inventa(self):
        f = [{"test": "a.mjs", "workflow": "w.yml", "jobs": 2, "toca_workflow": False, "hist": {"reloj_s": 372, "facturable_min": 2, "cola_s": 5, "n": 3}},
             {"test": "b.mjs", "workflow": "w2.yml", "jobs": 1, "toca_workflow": True, "hist": {}},
             {"test": "c.mjs", "workflow": None, "jobs": 0, "toca_workflow": False, "hist": None}]
        t = C.tabla(f, scopes={"repo"})
        self.assertIn("reloj ~6m12s / facturable ~2 min / cola ~5 s (n=3)", t)
        self.assertIn("sin historial de ejecuciones correctas: no se estima", t); self.assertIn("BLOQUEADO hasta `gh auth refresh -s workflow`", t)
        self.assertIn("SOLO LOCAL", t); self.assertNotIn("BLOQUEADO", C.tabla(f[:1], scopes={"repo"}))
        self.assertIn("1 workflow(s) distintos" if False else "2 workflow(s) distintos", t)


if __name__ == "__main__":
    unittest.main(verbosity=1)
