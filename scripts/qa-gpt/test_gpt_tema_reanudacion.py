import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones offline de paradas, caidas y reanudacion del pipeline QA GPT."""

import datetime as dt
import json
import os
import sqlite3
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import qa_gpt as Q
import qa_lote as L
import qa_pr as P
import qa_supervisor as S


def git(repo, *args, check=True):
    result = subprocess.run(
        ["git", *map(str, args)],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    if check and result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.remote = self.base / "origin.git"

        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "README.md").write_text("base\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(
            self.repo, "-c", "user.name=QA",
            "-c", "user.email=qa@example.invalid",
            "commit", "-qm", "base",
        )
        git(self.base, "clone", "-q", "--bare", self.repo, self.remote)
        git(self.repo, "remote", "add", "origin", self.remote)

        self.original = {
            "ROOT": Q.ROOT,
            "STATE": Q.STATE,
            "DB_PATH": Q.DB_PATH,
            "WT": Q.WT,
            "LOCK": Q.Lock.path,
            "REPO_QA": S.REPO_QA,
        }
        self.addCleanup(self.restore)

        Q.ROOT = self.repo
        Q.STATE = self.base / "state"
        Q.DB_PATH = Q.STATE / "estado.db"
        Q.WT = Q.STATE / "wt"
        Q.Lock.path = Q.STATE / "worker.lock"
        S.REPO_QA = self.repo
        Q.STATE.mkdir(parents=True)

        self.c = Q.db()
        self.addCleanup(self.c.close)

    def restore(self):
        Q.ROOT = self.original["ROOT"]
        Q.STATE = self.original["STATE"]
        Q.DB_PATH = self.original["DB_PATH"]
        Q.WT = self.original["WT"]
        Q.Lock.path = self.original["LOCK"]
        S.REPO_QA = self.original["REPO_QA"]

    def supervisor(self):
        return S.Supervisor(
            Q,
            out=lambda *args: None,
            claude=lambda *args, **kwargs: {
                "resultado": "no_se_puede",
                "causa": "",
                "resumen": "",
            },
        )

    def lote(self):
        gh = Mock()
        gh.ok.return_value = True
        return L.Lote(
            Q,
            gh=gh,
            runner=lambda *args, **kwargs: (0, ""),
            sleep=lambda _: None,
            out=lambda *args: None,
        )

    def propuesta(self, estado="propuesta", area="zona:reanudacion",
                  datos=None, rama=None):
        datos = datos if datos is not None else {
            "categoria": "regresion",
            "ficheros_nuevos": [],
        }
        cur = self.c.execute(
            """
            INSERT INTO propuestas
                (huella,area,titulo,datos,estado,rama,creado,actualizado)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                f"huella-{time.monotonic_ns()}",
                area,
                "Prueba de reanudacion",
                json.dumps(datos),
                estado,
                rama,
                Q.now(),
                Q.now(),
            ),
        )
        self.c.commit()
        return cur.lastrowid

    def rama(self, nombre="gpt-qa/reanudacion", estado="preparada",
             sha=None, area="zona:reanudacion"):
        sha = sha or git(self.repo, "rev-parse", "HEAD")
        self.c.execute(
            """
            INSERT INTO ramas(rama,area,ruta,sha,estado)
            VALUES (?,?,?,?,?)
            """,
            (nombre, area, str(self.repo), sha, estado),
        )
        self.c.commit()
        return nombre

    def job(self, clave, estado="pendiente", tipo="B",
            payload=None, area="zona:reanudacion"):
        payload = payload if payload is not None else {"ids": []}
        self.c.execute(
            """
            INSERT INTO jobs
                (clave,tipo,area,estado,payload,creado,actualizado,no_antes)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                clave, tipo, area, estado,
                json.dumps(payload), Q.now(), Q.now(), Q.now(),
            ),
        )
        self.c.commit()

    def estado(self, tabla, ident):
        return self.c.execute(
            f"SELECT estado FROM {tabla} WHERE id=?",
            (ident,),
        ).fetchone()[0]


class TestLocks(Base):
    def test_worker_recupera_lock_de_pid_muerto(self):
        """Evita que un proceso muerto bloquee INICIAR indefinidamente."""
        Q.Lock.path.write_text(
            "999999 2000-01-01T00:00:00",
            encoding="utf-8",
        )
        with patch.object(Q, "pid_alive", return_value=False):
            with Q.Lock():
                self.assertEqual(
                    int(Q.Lock.path.read_text().split()[0]),
                    os.getpid(),
                )
        self.assertFalse(Q.Lock.path.exists())

    def test_worker_rechaza_segundo_proceso_vivo(self):
        """Impide dos trabajadores simultaneos sobre estado.db."""
        Q.Lock.path.write_text(
            f"12345 {Q.now()}",
            encoding="utf-8",
        )
        with patch.object(Q, "pid_alive", return_value=True):
            with self.assertRaises(SystemExit):
                with Q.Lock():
                    pass
        self.assertEqual(
            Q.Lock.path.read_text().split()[0],
            "12345",
        )

    def test_worker_suelta_lock_tras_excepcion(self):
        """Una excepcion ordinaria no deja retenido el lock del worker."""
        with self.assertRaises(RuntimeError):
            with Q.Lock():
                raise RuntimeError("fallo simulado")
        self.assertFalse(Q.Lock.path.exists())

    def test_worker_suelta_lock_tras_keyboardinterrupt(self):
        """Ctrl+C libera el lock y permite iniciar otro trabajador."""
        with self.assertRaises(KeyboardInterrupt):
            with Q.Lock():
                raise KeyboardInterrupt()
        self.assertFalse(Q.Lock.path.exists())

    def test_lote_recupera_lock_de_proceso_muerto(self):
        """EJECUTAR puede arrancar despues de una terminacion abrupta."""
        lock = Q.STATE / "lote.lock"
        lock.write_text("999999 2000-01-01T00:00:00")
        with patch.object(Q, "pid_alive", return_value=False):
            with L.LoteLock(Q):
                self.assertEqual(
                    int(lock.read_text().split()[0]),
                    os.getpid(),
                )
        self.assertFalse(lock.exists())

    def test_lote_no_admite_dos_ejecutores(self):
        """Una segunda ventana de EJECUTAR no duplica envios."""
        lock = Q.STATE / "lote.lock"
        lock.write_text(f"12345 {Q.now()}")
        with patch.object(Q, "pid_alive", return_value=True):
            with self.assertRaises(SystemExit):
                with L.LoteLock(Q):
                    pass
        self.assertTrue(lock.exists())

    def test_lote_suelta_lock_tras_keyboardinterrupt(self):
        """Una interrupcion de consola no bloquea el siguiente lote."""
        lock = Q.STATE / "lote.lock"
        with self.assertRaises(KeyboardInterrupt):
            with L.LoteLock(Q):
                raise KeyboardInterrupt()
        self.assertFalse(lock.exists())


class TestJobsInterrumpidos(Base):
    def test_reconciliar_reencola_propuesta_huerfana(self):
        """Una propuesta sin job vivo vuelve a la cola tras una caida."""
        pid = self.propuesta()
        Q.reconciliar(self.c)
        jobs = self.c.execute(
            "SELECT * FROM jobs WHERE tipo='B'"
        ).fetchall()
        self.assertEqual(len(jobs), 1)
        self.assertIn(pid, json.loads(jobs[0]["payload"])["ids"])

    def test_reconciliar_no_duplica_job_vivo(self):
        """Rearrancar dos veces no multiplica los jobs pendientes."""
        pid = self.propuesta()
        Q.reconciliar(self.c)
        Q.reconciliar(self.c)
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM jobs WHERE tipo='B'"
            ).fetchone()[0],
            1,
        )
        self.assertEqual(self.estado("propuestas", pid), "propuesta")

    def test_reconciliar_conserva_job_en_curso(self):
        """Un job en curso no se sustituye por otro con el mismo trabajo."""
        pid = self.propuesta()
        self.job("B:ocupado", "en_curso", payload={"ids": [pid]})
        Q.reconciliar(self.c)
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM jobs WHERE tipo='B'"
            ).fetchone()[0],
            1,
        )

    def test_job_fallido_no_impide_reencolar(self):
        """Una clave antigua fallida no hace desaparecer la propuesta."""
        pid = self.propuesta()
        self.job("B:fallido", "fallido", payload={"ids": [pid]})
        Q.reconciliar(self.c)
        vivos = self.c.execute(
            """
            SELECT payload FROM jobs
            WHERE tipo='B' AND estado='pendiente'
            """
        ).fetchall()
        self.assertEqual(len(vivos), 1)
        self.assertIn(pid, json.loads(vivos[0][0])["ids"])

    def test_revision_no_supera_tres_intentos(self):
        """Una revision fallida repetida no produce reintentos infinitos."""
        pid = self.propuesta(estado="revisar")
        for n in range(1, 4):
            self.job(
                f"R:zona:reanudacion:{pid}:{n}",
                "fallido",
                tipo="R",
                payload={"id": pid},
            )
        Q.reconciliar(self.c)
        self.assertEqual(self.estado("propuestas", pid), "bloqueada")
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM jobs WHERE tipo='R'"
            ).fetchone()[0],
            3,
        )

    def test_enqueue_idempotente_tras_reinicio(self):
        """Repetir una insercion no crea dos trabajos con la misma clave."""
        args = ("B", "zona:reanudacion", {"ids": [1]}, "clave-unica")
        self.assertTrue(Q.enqueue(self.c, *args))
        self.assertFalse(Q.enqueue(self.c, *args))
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM jobs WHERE clave='clave-unica'"
            ).fetchone()[0],
            1,
        )

    def test_transaccion_sqlite_interrumpida_hace_rollback(self):
        """Una caida antes del commit no deja media transaccion persistida."""
        self.c.execute("BEGIN")
        self.c.execute(
            """
            INSERT INTO jobs(clave,tipo,area,estado,payload)
            VALUES ('sin-commit','B','zona:x','pendiente','{}')
            """
        )
        self.c.rollback()
        with sqlite3.connect(Q.DB_PATH) as otra:
            self.assertEqual(
                otra.execute(
                    "SELECT COUNT(*) FROM jobs WHERE clave='sin-commit'"
                ).fetchone()[0],
                0,
            )


class TestLotesReanudables(Base):
    def test_abrir_lote_reutiliza_en_curso(self):
        """Un lote interrumpido conserva su identificador al reabrirse."""
        lo = self.lote()
        primero = lo.abrir_lote()
        segundo = lo.abrir_lote()
        self.assertEqual(primero, segundo)
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM lotes WHERE estado='en_curso'"
            ).fetchone()[0],
            1,
        )

    def test_captura_reanudada_no_duplica_item(self):
        """Una captura repetida no incorpora dos veces la misma rama."""
        nombre = self.rama()
        pid = self.propuesta(estado="preparada", rama=nombre)
        lo = self.lote()

        with patch.object(Q, "reparar_perdidas", return_value=0):
            lid = lo.abrir_lote()
            lo.capturar(lid)
            lo.abrir_lote()

        items = lo.items(lid)
        self.assertEqual(len(items), 1)
        self.assertEqual(json.loads(items[0]["propuestas"]), [pid])

    def test_captura_recupera_rama_preparada_despues(self):
        """Una rama creada durante EJECUTAR entra en el lote abierto."""
        lo = self.lote()
        lid = lo.abrir_lote()

        nombre = self.rama()
        pid = self.propuesta(estado="preparada", rama=nombre)

        with patch.object(Q, "reparar_perdidas", return_value=0):
            self.assertEqual(lo.abrir_lote(), lid)

        items = lo.items(lid)
        self.assertEqual(len(items), 1)
        self.assertIn(pid, json.loads(items[0]["propuestas"]))

    def test_captura_aprueba_propuesta_una_sola_vez(self):
        """Reanudar la captura no repite la autorizacion de una propuesta."""
        nombre = self.rama()
        pid = self.propuesta(estado="preparada", rama=nombre)
        lo = self.lote()

        with patch.object(Q, "reparar_perdidas", return_value=0):
            lid = lo.abrir_lote()
            lo.capturar(lid)

        self.assertEqual(self.estado("propuestas", pid), "aprobada")
        self.assertEqual(len(lo.items(lid)), 1)

    def test_lote_vacio_se_puede_cerrar(self):
        """Una parada antes de capturar trabajo no deja lote colgado."""
        lo = self.lote()
        lid = lo.abrir_lote()
        with patch.object(lo, "panel", return_value=None):
            self.assertTrue(lo.cerrar_lote(lid))
        self.assertEqual(self.estado("lotes", lid), "cerrado")

    def test_lote_con_item_pendiente_no_se_cierra(self):
        """Una parada parcial conserva el lote para la siguiente ejecucion."""
        lo = self.lote()
        lid = lo.abrir_lote()
        nombre = self.rama()
        pid = self.propuesta(estado="preparada", rama=nombre)

        with patch.object(Q, "reparar_perdidas", return_value=0):
            lo.capturar(lid)

        with patch.object(lo, "panel", return_value=None):
            self.assertFalse(lo.cerrar_lote(lid))

        self.assertEqual(self.estado("lotes", lid), "en_curso")
        self.assertEqual(len(lo.items(lid)), 1)
        self.assertEqual(self.estado("propuestas", pid), "aprobada")


class TestWorktrees(Base):
    def test_worktree_reutiliza_rama_creada_antes_de_caida(self):
        """Una rama creada antes de fallar worktree add no bloquea el reintento."""
        nombre = "gpt-qa/recuperacion"
        base = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "branch", nombre, base)
        wt = Q.WT / "recuperacion"

        Q.wt_rama(nombre, wt, base)
        try:
            self.assertTrue(wt.exists())
            self.assertTrue((wt / ".git").exists())
        finally:
            Q.quitar_wt(wt)

        self.assertFalse(wt.exists())

    def test_worktree_limpieza_tras_interrupcion(self):
        """Un checkout temporal se elimina sin borrar su rama persistente."""
        nombre = "gpt-qa/interrumpido"
        wt = Q.WT / "interrumpido"
        base = git(self.repo, "rev-parse", "HEAD")

        try:
            Q.wt_rama(nombre, wt, base)
            raise KeyboardInterrupt()
        except KeyboardInterrupt:
            Q.quitar_wt(wt)

        self.assertFalse(wt.exists())
        self.assertEqual(
            git(self.repo, "show-ref", "--verify",
                f"refs/heads/{nombre}", check=False) != "",
            True,
        )

    def test_worktree_eliminacion_repetida_es_segura(self):
        """Una limpieza repetida tras reinicio no falla por directorio ausente."""
        wt = Q.WT / "inexistente"
        Q.quitar_wt(wt)
        Q.quitar_wt(wt)
        self.assertFalse(wt.exists())

    def test_supervisor_conserva_worktree_sucio(self):
        """La limpieza por disco lleno no destruye cambios sin confirmar."""
        wt = Q.STATE / "wt" / "sucio"
        wt.parent.mkdir(parents=True, exist_ok=True)
        git(self.repo, "worktree", "add", "-q", "--detach", wt, "HEAD")
        (wt / "README.md").write_text("trabajo pendiente\n")

        antiguo = time.time() - 8 * 3600
        os.utime(wt, (antiguo, antiguo))

        sup = self.supervisor()
        sup.cfg["disco_min_gb"] = 10 ** 9
        sup.liberar_disco()

        self.assertTrue(wt.exists())
        self.assertEqual(
            (wt / "README.md").read_text(),
            "trabajo pendiente\n",
        )

    def test_supervisor_limpia_worktree_viejo_sin_cambios(self):
        """Un worktree limpio abandonado no consume disco indefinidamente."""
        wt = Q.STATE / "wt" / "abandonado"
        wt.parent.mkdir(parents=True, exist_ok=True)
        git(self.repo, "worktree", "add", "-q", "--detach", wt, "HEAD")

        antiguo = time.time() - 8 * 3600
        os.utime(wt, (antiguo, antiguo))

        sup = self.supervisor()
        sup.cfg["disco_min_gb"] = 10 ** 9
        sup.liberar_disco()

        self.assertFalse(wt.exists())


class TestSupervisorReanudacion(Base):
    def test_ciclo_json_viejo_detecta_flujo_parado(self):
        """Detecta un flujo PR que sigue sin completar pasos durante horas."""
        carpeta = Q.STATE / "lote"
        carpeta.mkdir(parents=True)
        log = carpeta / "ejecutar.log"
        ciclo = carpeta / "ciclo.json"

        log.write_text("EJECUTAR activo\n")
        ciclo.write_text(json.dumps({"estado": "en_curso"}))

        viejo = time.time() - 3 * 3600
        os.utime(ciclo, (viejo, viejo))

        self.assertIn(
            "flujo PR",
            self.supervisor().flujo_pr_parado(),
        )

    def test_ciclo_viejo_sin_ejecutor_no_es_atasco(self):
        """Un ciclo historico no provoca reparaciones si EJECUTAR esta parado."""
        carpeta = Q.STATE / "lote"
        carpeta.mkdir(parents=True)
        log = carpeta / "ejecutar.log"
        ciclo = carpeta / "ciclo.json"

        log.write_text("ejecucion antigua\n")
        ciclo.write_text("{}")

        viejo = time.time() - 3 * 3600
        os.utime(log, (viejo, viejo))
        os.utime(ciclo, (viejo, viejo))

        self.assertIsNone(self.supervisor().flujo_pr_parado())

    def test_supervisor_no_repara_keyboardinterrupt(self):
        """Ctrl+C no se interpreta como defecto reparable por Claude."""
        sup = self.supervisor()
        sup._hijo = lambda args: (
            1,
            "Traceback (most recent call last):\nKeyboardInterrupt\n",
        )
        sup.reparar_codigo = Mock(
            side_effect=AssertionError("No debe llamar a Claude")
        )
        sup.cfg["vigilar_s"] = 3600

        self.assertEqual(sup.ejecutar(["iniciar"]), 1)
        sup.reparar_codigo.assert_not_called()

    def test_supervisor_reinicia_sin_reparar_codigo(self):
        """Una peticion explicita de reinicio no genera reparaciones falsas."""
        sup = self.supervisor()
        salidas = iter([(S.REINICIO, ""), (0, "")])
        sup._hijo = lambda args: next(salidas)
        sup.reparar_codigo = Mock(
            side_effect=AssertionError("No debe reparar")
        )

        self.assertEqual(sup.ejecutar(["servicio"]), 0)
        sup.reparar_codigo.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
