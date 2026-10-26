import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import datetime as dt
import json
import os
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

import qa_gpt as q
import itertools

_CLAVES = itertools.count()  # time.monotonic_ns() se repite en Windows entre llamadas seguidas


class TestQAGPT(unittest.TestCase):
    """Regresiones del worker INICIAR, con estado y dependencias aislados."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

        self.root = Path(self.tmp.name)
        self.state = self.root / "state"
        self.state.mkdir()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.wt = self.state / "wt"
        self.wt.mkdir()

        for name, value in (
            ("STATE", self.state),
            ("DB_PATH", self.state / "estado.db"),
            ("ROOT", self.repo),
            ("WT", self.wt),
            ("SVC", self.state / "servicio.json"),
        ):
            if hasattr(q, name):
                p = patch.object(q, name, value)
                p.start()
                self.addCleanup(p.stop)

        p = patch.object(q.Lock, "path", self.state / "worker.lock")
        p.start()
        self.addCleanup(p.stop)

        self.c = q.db()
        self.addCleanup(self.c.close)

    def job(
        self,
        tipo="A",
        area="familia:prueba",
        payload=None,
        estado="pendiente",
        intentos=0,
        **extra,
    ):
        payload = {} if payload is None else payload
        clave = f"test:{next(_CLAVES)}"

        cur = self.c.execute(
            """
            INSERT INTO jobs
                (clave,tipo,area,estado,payload,intentos,
                 no_antes,creado,actualizado)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                clave,
                tipo,
                area,
                estado,
                json.dumps(payload),
                intentos,
                q.now(),
                q.now(),
                q.now(),
            ),
        )
        jid = cur.lastrowid

        if extra:
            sets = ",".join(f"{k}=?" for k in extra)
            self.c.execute(
                f"UPDATE jobs SET {sets} WHERE id=?",
                (*extra.values(), jid),
            )

        self.c.commit()
        return jid

    def row(self, jid):
        return self.c.execute(
            "SELECT * FROM jobs WHERE id=?", (jid,)
        ).fetchone()

    def propuesta(self, estado="propuesta", revision=False):
        datos = {
            "titulo": "Contrato de prueba",
            "ficheros_nuevos": [],
        }
        if revision:
            datos["revision"] = 1

        cur = self.c.execute(
            """
            INSERT INTO propuestas
                (huella,area,titulo,datos,estado,creado,actualizado)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                f"huella-{time.monotonic_ns()}",
                "zona:prueba",
                "Contrato de prueba",
                json.dumps(datos),
                estado,
                q.now(),
                q.now(),
            ),
        )
        self.c.commit()
        return cur.lastrowid

    def test_enqueue_idempotente(self):
        """No duplica jobs tras repetir una operación."""
        self.assertTrue(
            q.enqueue(self.c, "A", "zona:x", {"sha": "abc"}, "A:x:abc")
        )
        self.assertFalse(
            q.enqueue(self.c, "A", "zona:x", {"sha": "abc"}, "A:x:abc")
        )
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM jobs WHERE clave='A:x:abc'"
            ).fetchone()[0],
            1,
        )

    def test_enqueue_no_oculta_error_de_disco(self):
        """Un fallo SQLite no debe confundirse con un duplicado."""

        class ConexionRota:
            def execute(self, *args, **kwargs):
                raise sqlite3.OperationalError("database is locked")

        with self.assertRaises(sqlite3.OperationalError):
            q.enqueue(
                ConexionRota(),
                "A",
                "zona:x",
                {},
                "A:fallo-disco",
            )

    def test_next_job_respeta_backoff(self):
        """No ejecuta trabajos aplazados antes de tiempo."""
        futuro = (
            dt.datetime.fromisoformat(q.now())
            + dt.timedelta(hours=2)
        ).isoformat()

        aplazado = self.job(
            "A", "zona:aplazada", no_antes=futuro
        )
        disponible = self.job("A", "zona:disponible")

        elegido = q.next_job(self.c)

        self.assertIsNotNone(elegido)
        self.assertEqual(elegido["id"], disponible)
        self.assertNotEqual(elegido["id"], aplazado)

    def test_next_job_prioriza_chat_reanudable(self):
        """Prioriza un chat persistido frente a una consulta nueva."""
        nuevo = self.job("A", "zona:nueva")
        anterior = self.job(
            "A",
            "zona:anterior",
            fase="generando",
            chat_id="chat-persistido",
        )

        elegido = q.next_job(self.c)

        self.assertEqual(elegido["id"], anterior)
        self.assertNotEqual(elegido["id"], nuevo)
        self.assertEqual(elegido["chat_id"], "chat-persistido")

    def test_next_job_prioriza_pass_b(self):
        """Prioriza la validación de propuestas frente a PASS A."""
        self.job("A", "zona:nueva")
        b = self.job("B", "zona:validacion", {"ids": [123]})

        self.assertEqual(q.next_job(self.c)["id"], b)

    def test_reconciliar_recupera_propuesta_huerfana(self):
        """Recupera propuestas cuyo job PASS B desapareció."""
        pid = self.propuesta()

        q.reconciliar(self.c)

        jobs = self.c.execute(
            "SELECT tipo,payload FROM jobs WHERE tipo='B'"
        ).fetchall()

        self.assertEqual(len(jobs), 1)
        self.assertIn(pid, json.loads(jobs[0]["payload"])["ids"])

        r = self.c.execute(
            "SELECT estado,siguiente FROM propuestas WHERE id=?",
            (pid,),
        ).fetchone()

        self.assertEqual(r["estado"], "propuesta")
        self.assertTrue(r["siguiente"])

    def test_reconciliar_no_duplica_job_vivo(self):
        """La reconciliación repetida no crea PASS B duplicados."""
        pid = self.propuesta()
        self.job(
            "B",
            "zona:prueba",
            {"ids": [pid]},
            estado="pendiente",
        )

        q.reconciliar(self.c)
        q.reconciliar(self.c)

        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM jobs WHERE tipo='B'"
            ).fetchone()[0],
            1,
        )

    def test_reconciliar_bloquea_revision_agotada(self):
        """No permite ciclos infinitos de revisión."""
        pid = self.propuesta("revisar", revision=True)

        q.reconciliar(self.c)

        r = self.c.execute(
            "SELECT estado,siguiente FROM propuestas WHERE id=?",
            (pid,),
        ).fetchone()

        self.assertEqual(r["estado"], "bloqueada")
        self.assertTrue(r["siguiente"])

    def test_revision_tiene_tres_intentos_maximo(self):
        """Las revisiones fallidas tienen un límite de reintentos."""
        pid = self.propuesta("revisar")

        for intento in range(3):
            self.assertTrue(
                q.enqueue_revision(self.c, "zona:prueba", pid)
            )
            self.c.execute(
                "UPDATE jobs SET estado='error' WHERE tipo='R'"
            )
            self.c.commit()

        self.assertFalse(
            q.enqueue_revision(self.c, "zona:prueba", pid)
        )
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM jobs WHERE tipo='R'"
            ).fetchone()[0],
            3,
        )

    def test_fallo_agota_reintentos(self):
        """Un trabajo agotado termina en error."""
        jid = self.job(
            "A", intentos=q.CFG["reintentos"] + 1
        )

        with patch.object(q, "escalar_a_claude", return_value=None):
            q.fallo(self.c, {"id": jid}, "error persistente")

        r = self.row(jid)
        self.assertEqual(r["estado"], "error")
        self.assertIn("error persistente", r["error"])

    def test_fallo_conserva_respuesta_capturada(self):
        """Conserva una respuesta persistida si falla su ingesta."""
        fichero = self.state / "respuesta.txt"
        fichero.write_text(
            '{"propuestas":[]}', encoding="utf-8"
        )

        jid = self.job(
            "A",
            intentos=1,
            respuesta=str(fichero),
            fase="capturada",
            chat_id="chat-original",
        )

        q.fallo(
            self.c,
            {"id": jid},
            "ingesta: database is locked",
            nuevo_chat=False,
        )

        r = self.row(jid)

        self.assertEqual(r["respuesta"], str(fichero))
        self.assertEqual(r["chat_id"], "chat-original")
        self.assertEqual(r["fase"], "capturada")
        self.assertEqual(r["estado"], "pendiente")

    def test_fallo_chat_nuevo_limpia_identificadores(self):
        """No reutiliza identificadores de un chat descartado."""
        jid = self.job(
            "A",
            intentos=1,
            respuesta=str(self.state / "vieja.txt"),
            fase="capturada",
            chat_id="chat-invalido",
        )

        q.fallo(
            self.c,
            {"id": jid},
            "respuesta invalida",
            nuevo_chat=True,
        )

        r = self.row(jid)

        self.assertIsNone(r["chat_id"])
        self.assertIsNone(r["fase"])
        self.assertIsNone(r["respuesta"])

    def test_fallo_inaccesible_reencola_solo_una_vez(self):
        """La recuperación de chats inaccesibles no es infinita."""
        jid = self.job(
            "A", intentos=q.CFG["reintentos"] + 1
        )

        with patch.object(q, "escalar_a_claude", return_value=None):
            q.fallo(self.c, {"id": jid}, "chat inaccesible")

            primera = self.row(jid)
            self.assertEqual(primera["estado"], "pendiente")
            self.assertIn("[reencolado]", primera["error"])
            self.assertEqual(primera["intentos"], 0)

            self.c.execute(
                "UPDATE jobs SET intentos=? WHERE id=?",
                (q.CFG["reintentos"] + 1, jid),
            )
            self.c.commit()

            q.fallo(self.c, {"id": jid}, "chat inaccesible")

        segunda = self.row(jid)
        self.assertEqual(segunda["estado"], "error")
        self.assertIn("[reencolado]", segunda["error"])

    def test_lock_rechaza_otro_worker_vivo(self):
        """Impide dos workers simultáneos."""
        otro_pid = os.getpid() + 1000
        q.Lock.path.write_text(
            f"{otro_pid} {q.now()}", encoding="utf-8"
        )

        with patch.object(q, "pid_alive", return_value=True):
            with self.assertRaises(SystemExit):
                with q.Lock():
                    self.fail("El segundo worker obtuvo el lock")

    def test_lock_recupera_pid_muerto(self):
        """Recupera un lock cuyo proceso ya terminó."""
        q.Lock.path.write_text(
            f"99999999 {q.now()}", encoding="utf-8"
        )

        with patch.object(q, "pid_alive", return_value=False):
            with q.Lock():
                self.assertTrue(q.Lock.path.exists())
                self.assertEqual(
                    int(q.Lock.path.read_text().split()[0]),
                    os.getpid(),
                )

        self.assertFalse(q.Lock.path.exists())

    def test_lock_se_libera_ante_excepcion(self):
        """Libera el lock incluso si el worker falla."""
        with self.assertRaises(RuntimeError):
            with q.Lock():
                raise RuntimeError("fallo simulado")

        self.assertFalse(q.Lock.path.exists())


if __name__ == "__main__":
    unittest.main()
