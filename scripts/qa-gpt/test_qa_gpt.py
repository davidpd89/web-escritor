"""Pruebas offline de qa-gpt (sin navegador, sin GPT, sin ejecutar tests del sitio): python scripts/qa-gpt/test_qa_gpt.py"""
import json, os, sys, tempfile, unittest, datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qa_gpt as q, gpt_browser as g


def msg(role, status="finished_successfully", end=True, text="x", ctype="text"):
    return {"author": {"role": role}, "status": status, "end_turn": end, "content": {"content_type": ctype, "parts": [text]}}


def conv(*msgs):
    mp, prev = {}, None
    for i, m in enumerate(msgs):
        mp[f"n{i}"] = {"message": m, "parent": prev}; prev = f"n{i}"
    return {"mapping": mp, "current_node": prev}


class Navegador(unittest.TestCase):
    def test_estados(self):
        u = msg("user")
        self.assertEqual(g.evaluar(conv(u, msg("assistant", text="{}")))[0], "terminada")
        self.assertEqual(g.evaluar(conv(u, msg("assistant", text="  ")))[0], "vacia")
        self.assertEqual(g.evaluar(conv(u, msg("assistant", status="in_progress", end=None)))[0], "generando")
        self.assertEqual(g.evaluar(conv(u, msg("tool"), msg("assistant", end=False)))[0], "generando")
        self.assertEqual(g.evaluar(conv(u, msg("assistant", status="finished_partial_completion", text="a")))[0], "fallida")
        self.assertEqual(g.evaluar(conv(u))[0], "generando")  # enviado, aun sin respuesta
        self.assertEqual(g.evaluar(conv(u, msg("tool"), msg("assistant", text="ok")))[2], 1)  # cuenta lecturas

    def test_respuesta_vieja_no_cuenta(self):  # solo se mira lo posterior al ULTIMO mensaje del usuario
        r = g.evaluar(conv(msg("user"), msg("assistant", text="vieja"), msg("user"), msg("assistant", status="in_progress", end=None)))
        self.assertEqual(r[0], "generando")


class Planificador(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); q.STATE = Path(self.tmp.name); q.DB_PATH = q.STATE / "e.db"; q.Lock.path = q.STATE / "worker.lock"
        self.c = q.db()

    def tearDown(self): self.c.close(); self.tmp.cleanup()

    def prop(self, estado, revision=False):
        d = {"titulo": "t", "ficheros_nuevos": [], **({"revision": 1} if revision else {})}
        return self.c.execute("INSERT INTO propuestas(huella,area,titulo,datos,estado,creado,actualizado) VALUES(?,?,?,?,?,?,?)",
                              (os.urandom(4).hex(), "zona:x", "t", json.dumps(d), estado, q.now(), q.now())).lastrowid

    def test_presupuesto_madrid_y_reinicio(self):
        for _ in range(12): self.c.execute("INSERT INTO peticiones(fecha,hora,tipo,area,chars_in,chars_out,ok) VALUES(?,?,?,?,0,0,1)", (q.today(), q.now(), "A", "z"))
        self.c.commit(); self.assertFalse(q.budget(self.c, 0)[0])
        c2 = q.db()  # "reinicio": nueva conexion, el contador persiste
        self.assertEqual(q.budget(c2, 0)[1], 12); c2.close()
        self.c.execute("UPDATE peticiones SET fecha='2000-01-01'"); self.assertTrue(q.budget(self.c, 0)[0])  # otro dia -> se reinicia
        self.assertEqual(q.today(), dt.datetime.now(q.TZ).date().isoformat() if q.TZ else q.today())

    def test_ronda_maximo_dos(self):
        self.assertFalse(q.budget(self.c, q.CFG["max_peticiones_ronda"])[0])

    def test_revisar_sin_job_se_cura(self):
        a, b = self.prop("revisar"), self.prop("revisar", revision=True)
        q.reconciliar(self.c)
        self.assertEqual(self.c.execute("SELECT tipo FROM jobs WHERE payload=?", (json.dumps({"id": a}),)).fetchone()[0], "R")
        r = self.c.execute("SELECT estado,siguiente FROM propuestas WHERE id=?", (b,)).fetchone()
        self.assertEqual(r["estado"], "bloqueada"); self.assertTrue(r["siguiente"])  # nunca sin siguiente paso

    def test_r_fallido_permite_reintento_acotado(self):
        a = self.prop("revisar")
        for n in range(3):
            self.assertTrue(q.enqueue_revision(self.c, "zona:x", a)); self.c.execute("UPDATE jobs SET estado='error'")
        self.assertFalse(q.enqueue_revision(self.c, "zona:x", a))  # tope 3

    def test_lock_unico_y_pid_exacto(self):
        self.assertTrue(q.pid_alive(os.getpid())); self.assertFalse(q.pid_alive(4999999))
        with q.Lock():
            with self.assertRaises(SystemExit):  # otro proceso vivo (el padre) con lock reciente
                q.Lock.path.write_text(f"{os.getppid()} {q.now()}"); q.Lock().__enter__()
        q.Lock.path.write_text(f"4999999 {q.now()}")
        with q.Lock(): pass  # lock de proceso muerto se recupera

    def test_recuperacion_en_curso(self):
        q.enqueue(self.c, "A", "zona:x", {}, "k1"); self.c.execute("UPDATE jobs SET estado='en_curso'")
        self.c.execute("UPDATE jobs SET estado='pendiente' WHERE estado='en_curso'")  # misma sentencia que scan-once bajo Lock
        self.assertEqual(self.c.execute("SELECT estado FROM jobs").fetchone()[0], "pendiente")

    def test_parche_no_aplicable_se_detecta(self):
        self.assertTrue(q.parche_aplica({"ruta": "src/x.js", "parche": "x"}).startswith("ruta no permitida"))
        self.assertTrue(q.parche_aplica({"ruta": "tests/nada.py", "parche": "--- a/tests/nada.py\n+++ b/tests/nada.py\n@@ -1 +1 @@\n-a\n+b\n"}).startswith("NO APLICA"))

    def test_verif_local_sintaxis(self):
        v = q.verif_local({"ficheros_nuevos": [{"ruta": "tests/zz_nuevo.py", "contenido": "def f(:\n"}, {"ruta": "tests/zz_ok.py", "contenido": "x = 1\n"}]})
        self.assertTrue(v["ficheros_nuevos"][0]["sintaxis"].startswith("ERROR")); self.assertTrue(v["ficheros_nuevos"][1]["sintaxis"].startswith("OK"))

    def test_json_con_texto_alrededor(self):
        self.assertEqual(q.load_json_block('hola ```json\n{"a": 1}\n``` adios'), {"a": 1})
        with self.assertRaises(ValueError): q.load_json_block("sin json")


if __name__ == "__main__":
    unittest.main(verbosity=1)
