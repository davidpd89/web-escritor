"""Limite de uso de ChatGPT en qa_gpt.process: el job debe quedar pendiente con espera (antes: sqlite3.ProgrammingError por 3 valores para 4 marcadores)."""
import sys, tempfile, unittest, warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_gpt as Q
import gpt_browser as G


class LimiteChatGPT(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True); self.addCleanup(self.tmp.cleanup)
        self.o = (Q.STATE, Q.DB_PATH, Q.WT, Q.Lock.path, G.ask)
        Q.STATE = Path(self.tmp.name) / "state"; Q.DB_PATH = Q.STATE / "estado.db"; Q.WT = Q.STATE / "wt"; Q.Lock.path = Q.STATE / "worker.lock"
        Q.STATE.mkdir(parents=True); self.addCleanup(self.restore)
        self.c = Q.db(); self.addCleanup(self.c.close)

    def restore(self): Q.STATE, Q.DB_PATH, Q.WT, Q.Lock.path, G.ask = self.o

    def test_limite_deja_el_job_pendiente_con_espera_y_marca_de_limite(self):
        self.c.execute("INSERT INTO jobs(clave,tipo,area,estado,payload,creado,actualizado) VALUES('A:x','A','zona:x','pendiente','{}',?,?)", (Q.now(), Q.now())); self.c.commit()
        job = self.c.execute("SELECT * FROM jobs").fetchone()

        def ask(*a, **k): raise G.RateLimited("limite de uso de ChatGPT")
        G.ask = ask
        Q.prompt_for = lambda job, c: "prompt"
        with self.assertRaises(SystemExit):
            Q.process(job, self.c)
        r = self.c.execute("SELECT * FROM jobs").fetchone()
        self.assertEqual(r["estado"], "pendiente"); self.assertIn("limite", r["error"]); self.assertGreater(r["no_antes"], Q.now())
        self.assertTrue((Q.STATE / "limite").exists())


class SinAvisosDeSintaxis(unittest.TestCase):
    def test_qa_gpt_compila_sin_secuencias_de_escape_invalidas(self):
        """`C:\\GIT` y `\\`` en docstrings no raw eran SyntaxWarning (SyntaxError en versiones futuras de Python)."""
        src = (Path(__file__).resolve().parent / "qa_gpt.py").read_text(encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(src, "qa_gpt.py", "exec")


if __name__ == "__main__":
    unittest.main()
