"""Un 'database is locked' no deja la conexion con la transaccion (y su lock) abierta: el interbloqueo del 2026-10-26 paro el pipeline 20 min."""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_gpt as q


class TestBloqueo(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        for k, v in (("STATE", Path(tmp.name)), ("DB_PATH", Path(tmp.name) / "estado.db")):
            p = patch.object(q, k, v); p.start(); self.addCleanup(p.stop)

    def test_error_de_bloqueo_suelta_la_transaccion(self):
        a, b = q.db(), q.db(); self.addCleanup(a.close); self.addCleanup(b.close)
        self.assertEqual(a.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        b.execute("PRAGMA busy_timeout=50")
        a.execute("BEGIN IMMEDIATE"); a.execute("INSERT INTO jobs(clave) VALUES('x')")
        b.execute("SELECT count(*) FROM jobs").fetchone()  # en WAL el lector no espera al escritor
        with self.assertRaises(sqlite3.OperationalError): b.execute("INSERT INTO jobs(clave) VALUES('y')")
        self.assertFalse(b.in_transaction)  # sin el arreglo seguia abierta y bloqueaba a los demas
        a.commit()
        b.execute("INSERT INTO jobs(clave) VALUES('y')"); b.commit()
        self.assertEqual(a.execute("SELECT count(*) FROM jobs").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
