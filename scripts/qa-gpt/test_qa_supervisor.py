"""Supervisor: caida -> Claude repara en worktree -> suite verde -> fast-forward del codigo vivo -> relanza; limites anti-bucle; atasco."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_gpt as q
import qa_supervisor as S

TB = '''Traceback (most recent call last):
  File "C:\\GIT\\web-escritor-qa-gpt\\scripts\\qa-gpt\\qa_gpt.py", line 173, in area_stats
    sha = git("log", "-1", "--format=%h", "--", *src, check=False) if src else ""
  File "C:\\Users\\x\\Python311\\Lib\\subprocess.py", line 1538, in _execute_child
    hp, ht, pid, tid = _winapi.CreateProcess(executable, args,
FileNotFoundError: [WinError 206] El nombre del archivo o la extension es demasiado largo
'''


def g(*a, cwd):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


class Base(unittest.TestCase):
    def setUp(self):
        orig = (q.STATE, q.DB_PATH, q.Lock.path)
        self.addCleanup(lambda: (setattr(q, "STATE", orig[0]), setattr(q, "DB_PATH", orig[1]), setattr(q.Lock, "path", orig[2])))
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True); t = Path(self.tmp.name)
        q.STATE = t / "state"; q.DB_PATH = q.STATE / "e.db"; q.Lock.path = q.STATE / "worker.lock"
        self.addCleanup(self.tmp.cleanup)
        # repo de juguete con la misma forma que el real: scripts/qa-gpt/<modulo>.py y su test
        self.repo = t / "repo"; cod = self.repo / "scripts" / "qa-gpt"; cod.mkdir(parents=True)
        (cod / "m.py").write_text("def f(): return 1\n"); (cod / "test_m.py").write_text("import unittest, m\nclass T(unittest.TestCase):\n    def test(self): self.assertEqual(m.f(), 1)\n")
        g("init", "-q", "-b", "automation/qa-gpt", cwd=self.repo); g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base", "--allow-empty", cwd=self.repo)
        g("add", "-A", cwd=self.repo); g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "m", cwd=self.repo)
        self.orig_repo = S.REPO_QA; S.REPO_QA = self.repo; self.addCleanup(lambda: setattr(S, "REPO_QA", self.orig_repo))
        self.llamadas = []

    def sup(self, editar=None, resultado="corregido"):
        def claude(clave, sistema, entrada, herramientas, cwd):
            self.llamadas.append((clave, entrada, herramientas, Path(cwd)))
            if editar: editar(Path(cwd))
            return {"resultado": resultado, "causa": "causa x", "resumen": "arreglado"}
        return S.Supervisor(q, out=lambda *_: None, claude=claude)


class Reparacion(Base):
    def test_firma_estable_sin_numeros_de_linea(self):
        self.assertEqual(S.firma(TB), "FileNotFoundError@qa_gpt.py:area_stats")
        self.assertEqual(S.firma(TB.replace("line 173", "line 999")), S.firma(TB))

    def test_corrige_con_suite_verde_e_integra_en_el_codigo_vivo(self):
        def editar(cod): (cod / "m.py").write_text("def f(): return 1  # arreglado\n")
        cache = self.repo / "scripts/qa-gpt/__pycache__"; cache.mkdir(); (cache / "m.cpython-311.pyc").write_bytes(b"x")  # el codigo vivo tiene cache sin seguimiento
        self.assertEqual(self.sup(editar).reparar_codigo(TB, "F@m"), "corregido")
        self.assertNotIn("__pycache__", g("show", "--name-only", "--format=", "HEAD", cwd=self.repo))  # la cache nunca entra en el commit
        self.assertIn("arreglado", (self.repo / "scripts/qa-gpt/m.py").read_text())  # fast-forward del codigo vivo
        self.assertIn("autofix(qa-gpt): causa x", g("log", "-1", "--format=%s", cwd=self.repo))
        self.assertIn("Bash(python -m unittest:*)", self.llamadas[0][2]); self.assertNotIn("Bash(git", self.llamadas[0][2])
        self.assertEqual(g("worktree", "list", "--porcelain", cwd=self.repo).count("worktree "), 1)  # worktree limpio

    def test_suite_roja_no_integra_nada(self):
        antes = g("rev-parse", "HEAD", cwd=self.repo)
        def editar(cod): (cod / "m.py").write_text("def f(): return 2\n")  # rompe el test
        self.assertEqual(self.sup(editar).reparar_codigo(TB, "F@m"), "suite_roja")
        self.assertEqual(g("rev-parse", "HEAD", cwd=self.repo), antes); self.assertIn("return 1", (self.repo / "scripts/qa-gpt/m.py").read_text())

    def test_misma_firma_una_vez_al_dia_y_tope_diario(self):
        s = self.sup(resultado="no_se_puede")
        self.assertEqual(s.reparar_codigo(TB, "F@m"), "no_se_puede")
        self.assertEqual(s.reparar_codigo(TB, "F@m"), "omitido"); self.assertEqual(len(self.llamadas), 1)
        s.cfg["max_reparaciones_dia"] = 2; s.reparar_codigo(TB, "G@m")
        self.assertEqual(s.reparar_codigo(TB, "H@m"), "omitido")

    def test_envoltorio_repara_y_relanza_y_sale_con_q(self):
        s = self.sup(); salidas = iter([(1, "x\n" + TB), (0, "")])  # cae una vez; luego el usuario pulsa Q (salida limpia)
        s._hijo = lambda args: next(salidas); reparadas = []; s.reparar_codigo = lambda tb, fir: reparadas.append(fir) or "corregido"
        s.cfg["vigilar_s"] = 3600; S.time.sleep, orig = (lambda _: None), S.time.sleep
        try: self.assertEqual(s.ejecutar(["iniciar"]), 0)
        finally: S.time.sleep = orig
        self.assertEqual(reparadas, ["FileNotFoundError@qa_gpt.py:area_stats"])

    def test_ctrl_c_no_es_un_fallo(self):
        s = self.sup(); s._hijo = lambda args: (1, "Traceback (most recent call last):\nKeyboardInterrupt\n"); s.reparar_codigo = lambda *a: self.fail("no debe reparar")
        s.cfg["vigilar_s"] = 3600; self.assertEqual(s.ejecutar(["iniciar"]), 1)


class ErrorRepetidoDelWorker(Base):
    def test_tercer_error_igual_se_encarga_y_reinicia(self):
        llamadas = []; orig = S.Supervisor.reparar_codigo
        S.Supervisor.reparar_codigo = lambda self_, tb, fir: llamadas.append(fir) or "corregido"
        self.addCleanup(lambda: setattr(S.Supervisor, "reparar_codigo", orig)); q._errores_seguidos.clear()
        def fallo():
            try: q.git("log", "--", *["x" * 200] * 400)  # mismo fallo cada vez
            except Exception: return q.escalar_error_repetido()
        orig_git = q.git; q.git = lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("[WinError 206]")); self.addCleanup(lambda: setattr(q, "git", orig_git))
        self.assertFalse(fallo()); self.assertFalse(fallo()); self.assertEqual(llamadas, [])
        self.assertTrue(fallo()); self.assertEqual(len(llamadas), 1)  # al 3o: Claude, y el servicio sale con REINICIO

    def test_reinicio_relanza_sin_reparar(self):
        s = self.sup(); salidas = iter([(S.REINICIO, ""), (0, "")]); s._hijo = lambda args: next(salidas)
        s.reparar_codigo = lambda *a: self.fail("no debe reparar"); self.assertEqual(s.ejecutar(["servicio"]), 0)


class Atasco(Base):
    def test_atasco_a_los_20_min_con_trabajo_ejecutable(self):
        c = q.db(); viejo = "2000-01-01T00:00:00"
        c.execute("INSERT INTO jobs(clave,tipo,area,estado,payload,creado,actualizado) VALUES('k','A','zona:x','pendiente','{}',?,?)", (viejo, viejo))
        c.execute("INSERT INTO eventos(fecha,entidad,ident,estado,nota) VALUES(?,'job',1,'x','')", (viejo,)); c.commit()
        s = self.sup(); self.assertEqual(s.cfg["atasco_min"], 20); self.assertIn("sin actividad", s.atasco())
        c.execute("UPDATE jobs SET no_antes='2999-01-01T00:00:00'"); c.commit()
        self.assertIsNone(s.atasco())  # en espera programada (backoff): no es atasco
        c.execute("UPDATE jobs SET no_antes=NULL"); c.execute("INSERT INTO eventos(fecha,entidad,ident,estado,nota) VALUES(?,'job',1,'x','')", (q.now(),)); c.commit(); c.close()
        self.assertIsNone(s.atasco())  # hubo actividad reciente

    def test_limite_de_chatgpt_no_es_atasco(self):
        c = q.db(); viejo = "2000-01-01T00:00:00"
        c.execute("INSERT INTO jobs(clave,tipo,area,estado,payload,creado,actualizado) VALUES('k','A','zona:x','pendiente','{}',?,?)", (viejo, viejo)); c.commit(); c.close()
        (Path(q.STATE) / "servicio.json").write_text(json.dumps({"estado": "pausado_limite"}))
        self.assertIsNone(self.sup().atasco())


if __name__ == "__main__":
    unittest.main()
