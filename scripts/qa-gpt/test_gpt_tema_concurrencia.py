import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Concurrencia offline entre INICIAR y EJECUTAR sobre una SQLite compartida."""

import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import qa_gpt as q
import qa_lote as L


class FakeGh:
    """GitHub aislado: ninguna operación puede alcanzar la red."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def forbidden(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            raise AssertionError("Acceso externo no permitido: " + name)
        return forbidden


class BaseConcurrencia(unittest.TestCase):
    """Aísla los globales persistentes y utiliza conexiones SQLite reales."""

    def setUp(self):
        original = (q.STATE, q.DB_PATH, q.Lock.path, q.ROOT, q.WT)
        self.addCleanup(
            lambda: (
                setattr(q, "STATE", original[0]),
                setattr(q, "DB_PATH", original[1]),
                setattr(q.Lock, "path", original[2]),
                setattr(q, "ROOT", original[3]),
                setattr(q, "WT", original[4]),
            )
        )

        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)

        base = Path(self.tmp.name)
        q.STATE = base / "state"
        q.DB_PATH = q.STATE / "estado.db"
        q.Lock.path = q.STATE / "worker.lock"
        q.ROOT = base / "src"
        q.WT = q.STATE / "wt"

        q.STATE.mkdir()
        q.ROOT.mkdir()

        self.c = q.db()
        self.addCleanup(self.c.close)

        self.gh = FakeGh()

    def conexion(self, timeout=0.2):
        c = sqlite3.connect(q.DB_PATH, timeout=timeout, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def lote(self, **cfg):
        obj = L.Lote(
            q,
            gh=self.gh,
            runner=lambda *args: (0, ""),
            sleep=lambda _: None,
            out=lambda _: None,
            cfg={
                "poll_s": 0,
                "max_horas": 0.001,
                "node_modules": str(q.STATE / "no-node-modules"),
                **cfg,
            },
        )
        self.addCleanup(obj.c.close)
        return obj

    def propuesta(self, nombre, rama=None, estado="preparada"):
        rama = rama or "gpt-qa/" + nombre
        datos = {
            "titulo": nombre,
            "categoria": "regresion",
            "ficheros_nuevos": [
                {
                    "ruta": "tests/test-" + nombre + ".py",
                    "contenido": "assert True\n",
                }
            ],
        }
        cur = self.c.execute(
            """
            INSERT INTO propuestas
            (huella,area,titulo,datos,estado,rama,creado,actualizado)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                nombre,
                "zona:concurrencia",
                nombre,
                json.dumps(datos),
                estado,
                rama,
                q.now(),
                q.now(),
            ),
        )
        self.c.commit()
        return cur.lastrowid

    def rama(self, nombre, sha=None):
        rama = "gpt-qa/" + nombre
        sha = sha or ("%040x" % (len(nombre) + 100))
        self.c.execute(
            """
            INSERT INTO ramas(rama,area,ruta,sha,estado)
            VALUES(?,?,?,?,?)
            """,
            (rama, "zona:concurrencia", "", sha, "preparada"),
        )
        self.c.commit()
        return rama, sha

    def item(self, lote, rama, sha, propuestas):
        clave = rama + "@" + sha[:12]
        self.c.execute(
            """
            INSERT INTO lote_items
            (clave,lote_id,rama,sha,area,propuestas,estado,runs,creado,actualizado)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                clave,
                lote,
                rama,
                sha,
                "zona:concurrencia",
                json.dumps(propuestas),
                "preparada",
                "{}",
                q.now(),
                q.now(),
            ),
        )
        self.c.commit()
        return clave

    def ejecutar_hilos(self, funciones, timeout=8):
        """Propaga excepciones y evita que un test quede esperando indefinidamente."""
        with ThreadPoolExecutor(max_workers=len(funciones)) as pool:
            futuros = [pool.submit(f) for f in funciones]
            return [f.result(timeout=timeout) for f in futuros]


class SQLiteConcurrencia(BaseConcurrencia):

    def test_01_dos_conexiones_comparten_estado(self):
        """Previene que INICIAR y EJECUTAR utilicen bases de datos distintas."""
        pid = self.propuesta("compartida")
        otra = self.conexion()
        try:
            fila = otra.execute(
                "SELECT estado FROM propuestas WHERE id=?", (pid,)
            ).fetchone()
            self.assertEqual(fila["estado"], "preparada")
        finally:
            otra.close()

    def test_02_escritura_no_confirmada_es_invisible(self):
        """Previene capturar una propuesta cuyo cambio todavía no se ha confirmado."""
        pid = self.propuesta("sin-commit")
        escritor = self.conexion()
        lector = self.conexion()
        try:
            escritor.execute("BEGIN IMMEDIATE")
            escritor.execute(
                "UPDATE propuestas SET estado='aceptada' WHERE id=?", (pid,)
            )
            estado = lector.execute(
                "SELECT estado FROM propuestas WHERE id=?", (pid,)
            ).fetchone()[0]
            self.assertEqual(estado, "preparada")
        finally:
            escritor.rollback()
            escritor.close()
            lector.close()

    def test_03_rollback_conserva_propuesta(self):
        """Previene pérdida de propuestas tras una caída durante una transacción."""
        pid = self.propuesta("rollback")
        c = self.conexion()
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("DELETE FROM propuestas WHERE id=?", (pid,))
            c.rollback()
            self.assertIsNotNone(
                self.c.execute(
                    "SELECT id FROM propuestas WHERE id=?", (pid,)
                ).fetchone()
            )
        finally:
            c.close()

    def test_04_escritores_compiten_sin_corromper_bd(self):
        """Previene corrupción de estado.db cuando dos escritores compiten."""
        barrera = threading.Barrier(2)
        resultados = []

        def escritor(numero):
            c = self.conexion(timeout=1)
            try:
                barrera.wait(timeout=3)
                c.execute("BEGIN IMMEDIATE")
                c.execute(
                    """
                    INSERT INTO analisis(area,fecha,head,fuente_sha)
                    VALUES(?,?,?,?)
                    """,
                    (str(numero), q.today(), "abc", "abc"),
                )
                c.commit()
                return numero
            finally:
                c.close()

        resultados = self.ejecutar_hilos(
            [lambda: escritor(1), lambda: escritor(2)]
        )
        self.assertEqual(set(resultados), {1, 2})
        self.assertEqual(
            self.c.execute("SELECT COUNT(*) FROM analisis").fetchone()[0], 2
        )
        self.assertEqual(
            self.c.execute("PRAGMA integrity_check").fetchone()[0], "ok"
        )

    def test_05_database_locked_no_deja_escritura_parcial(self):
        """Previene cambios parciales cuando SQLite devuelve database is locked."""
        pid = self.propuesta("locked")
        primero = self.conexion()
        segundo = self.conexion(timeout=0)
        try:
            primero.execute("BEGIN IMMEDIATE")
            primero.execute(
                "UPDATE propuestas SET estado='aceptada' WHERE id=?", (pid,)
            )
            with self.assertRaises(sqlite3.OperationalError):
                segundo.execute(
                    "UPDATE propuestas SET estado='aprobada' WHERE id=?",
                    (pid,),
                )
            segundo.rollback()
            primero.rollback()
            self.assertEqual(
                self.c.execute(
                    "SELECT estado FROM propuestas WHERE id=?", (pid,)
                ).fetchone()[0],
                "preparada",
            )
        finally:
            primero.close()
            segundo.close()

    def test_06_lectores_concurrentes_no_bloquean_consultas(self):
        """Previene bloqueos innecesarios al consultar el estado desde varios hilos."""
        for i in range(30):
            self.propuesta("lectura-%d" % i)

        def leer():
            c = self.conexion()
            try:
                return c.execute(
                    "SELECT COUNT(*) FROM propuestas"
                ).fetchone()[0]
            finally:
                c.close()

        self.assertEqual(
            self.ejecutar_hilos([leer for _ in range(8)]),
            [30] * 8,
        )

    def test_07_conexiones_cerradas_liberan_bloqueos(self):
        """Previene que una conexión terminada mantenga bloqueada la base."""
        c = self.conexion()
        c.execute("BEGIN IMMEDIATE")
        c.close()

        otra = self.conexion(timeout=0.5)
        try:
            otra.execute(
                "INSERT INTO analisis(area,fecha) VALUES(?,?)",
                ("liberada", q.today()),
            )
            otra.commit()
        finally:
            otra.close()

        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM analisis WHERE area='liberada'"
            ).fetchone()[0],
            1,
        )


class CapturaConcurrente(BaseConcurrencia):

    def test_08_captura_no_duplica_rama_en_mismo_lote(self):
        """Previene duplicar un item al repetir EJECUTAR sobre un lote abierto."""
        rama, sha = self.rama("captura")
        pid = self.propuesta("captura", rama)
        lo = self.lote()

        with patch.object(q, "reparar_perdidas", return_value=None):
            lid = lo.abrir_lote()
            lo.capturar(lid)
            lo.capturar(lid)

        clave = rama + "@" + sha[:12]
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM lote_items WHERE clave=?", (clave,)
            ).fetchone()[0],
            1,
        )
        self.assertEqual(
            json.loads(
                self.c.execute(
                    "SELECT propuestas FROM lote_items WHERE clave=?",
                    (clave,),
                ).fetchone()[0]
            ),
            [pid],
        )

    def test_09_captura_autoriza_propuesta_y_rama(self):
        """Previene divergencia entre el estado de propuestas y ramas tras EJECUTAR."""
        rama, _ = self.rama("autoriza")
        pid = self.propuesta("autoriza", rama)
        lo = self.lote()

        with patch.object(q, "reparar_perdidas", return_value=None):
            lo.abrir_lote()

        self.assertEqual(
            self.c.execute(
                "SELECT estado FROM propuestas WHERE id=?", (pid,)
            ).fetchone()[0],
            "aprobada",
        )
        self.assertEqual(
            self.c.execute(
                "SELECT estado FROM ramas WHERE rama=?", (rama,)
            ).fetchone()[0],
            "aprobada",
        )

    def test_10_nueva_rama_entra_en_lote_abierto(self):
        """Previene perder tests generados por INICIAR mientras EJECUTAR sigue activo."""
        lo = self.lote()
        with patch.object(q, "reparar_perdidas", return_value=None):
            lid = lo.abrir_lote()
            rama, sha = self.rama("tardia")
            self.propuesta("tardia", rama)
            lo.abrir_lote()

        self.assertEqual(
            self.c.execute(
                "SELECT lote_id FROM lote_items WHERE clave=?",
                (rama + "@" + sha[:12],),
            ).fetchone()[0],
            lid,
        )

    def test_11_hay_nuevo_detecta_generacion_posterior(self):
        """Previene cerrar el lote mientras INICIAR ha preparado trabajo nuevo."""
        lo = self.lote()
        self.assertFalse(lo.hay_nuevo())

        rama, _ = self.rama("posterior")
        self.propuesta("posterior", rama)

        self.assertTrue(lo.hay_nuevo())

    def test_12_misma_rama_no_se_captura_dos_veces(self):
        """Previene capturas repetidas de una rama ya registrada."""
        rama, sha = self.rama("unica")
        self.propuesta("unica", rama)
        lo = self.lote()

        with patch.object(q, "reparar_perdidas", return_value=None):
            lid = lo.abrir_lote()
            lo.capturar(lid)

        self.assertFalse(lo.hay_nuevo())
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM lote_items WHERE rama=? AND sha=?",
                (rama, sha),
            ).fetchone()[0],
            1,
        )


    def test_14_clave_duplicada_no_crea_segundo_item(self):
        """Previene duplicar un item aunque dos conexiones intenten insertarlo."""
        rama, sha = self.rama("constraint")
        lid = self.c.execute(
            "INSERT INTO lotes(inicio,estado) VALUES(?,?)",
            (q.now(), "en_curso"),
        ).lastrowid
        self.c.commit()
        clave = self.item(lid, rama, sha, [])

        otra = self.conexion()
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                otra.execute(
                    """
                    INSERT INTO lote_items
                    (clave,lote_id,rama,sha,estado)
                    VALUES(?,?,?,?,?)
                    """,
                    (clave, lid, rama, sha, "preparada"),
                )
            otra.rollback()
        finally:
            otra.close()

        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM lote_items WHERE clave=?", (clave,)
            ).fetchone()[0],
            1,
        )


class PersistenciaLote(BaseConcurrencia):

    def test_15_set_registra_estado_e_historial(self):
        """Previene perder la trazabilidad de un cambio confirmado."""
        rama, sha = self.rama("historial")
        lo = self.lote()
        lid = self.c.execute(
            "INSERT INTO lotes(inicio,estado) VALUES(?,?)",
            (q.now(), "en_curso"),
        ).lastrowid
        self.c.commit()
        clave = self.item(lid, rama, sha, [])

        lo.set(clave, "validacion_local", "iniciada")

        self.assertEqual(
            self.c.execute(
                "SELECT estado FROM lote_items WHERE clave=?", (clave,)
            ).fetchone()[0],
            "validacion_local",
        )
        self.assertEqual(
            self.c.execute(
                "SELECT estado FROM lote_hist WHERE clave=? ORDER BY rowid DESC",
                (clave,),
            ).fetchone()[0],
            "validacion_local",
        )

    def test_16_set_reintenta_bloqueo_transitorio(self):
        """Previene perder un estado cuando otro proceso bloquea SQLite brevemente."""
        rama, sha = self.rama("reintento")
        lo = self.lote()
        lid = self.c.execute(
            "INSERT INTO lotes(inicio,estado) VALUES(?,?)",
            (q.now(), "en_curso"),
        ).lastrowid
        self.c.commit()
        clave = self.item(lid, rama, sha, [])

        bloqueador = self.conexion()
        bloqueador.execute("BEGIN IMMEDIATE")

        intentos = []

        def liberar(_):
            intentos.append(1)
            bloqueador.rollback()

        lo.sleep = liberar
        lo.c.execute("PRAGMA busy_timeout=1")

        try:
            lo.set(clave, "local_ok", "recuperado")
        finally:
            bloqueador.close()

        self.assertGreaterEqual(len(intentos), 1)
        self.assertEqual(
            self.c.execute(
                "SELECT estado FROM lote_items WHERE clave=?", (clave,)
            ).fetchone()[0],
            "local_ok",
        )

    def test_17_set_agota_reintentos_sin_bucle_infinito(self):
        """Previene que database is locked provoque reintentos ilimitados."""
        rama, sha = self.rama("agotado")
        lo = self.lote()
        lid = self.c.execute(
            "INSERT INTO lotes(inicio,estado) VALUES(?,?)",
            (q.now(), "en_curso"),
        ).lastrowid
        self.c.commit()
        clave = self.item(lid, rama, sha, [])

        bloqueador = self.conexion()
        bloqueador.execute("BEGIN IMMEDIATE")
        lo.c.execute("PRAGMA busy_timeout=1")
        esperas = []
        lo.sleep = lambda _: esperas.append(1)

        try:
            with self.assertRaises(sqlite3.OperationalError):
                lo.set(clave, "local_ok", "bloqueado")
        finally:
            bloqueador.rollback()
            bloqueador.close()

        self.assertEqual(len(esperas), 5)
        self.assertEqual(
            self.c.execute(
                "SELECT estado FROM lote_items WHERE clave=?", (clave,)
            ).fetchone()[0],
            "preparada",
        )

    def test_18_historial_no_se_duplica_tras_reintento(self):
        """Previene registrar dos transiciones por una escritura reintentada."""
        rama, sha = self.rama("hist-unico")
        lo = self.lote()
        lid = self.c.execute(
            "INSERT INTO lotes(inicio,estado) VALUES(?,?)",
            (q.now(), "en_curso"),
        ).lastrowid
        self.c.commit()
        clave = self.item(lid, rama, sha, [])

        bloqueador = self.conexion()
        bloqueador.execute("BEGIN IMMEDIATE")
        lo.c.execute("PRAGMA busy_timeout=1")
        lo.sleep = lambda _: bloqueador.rollback()

        try:
            lo.set(clave, "local_ok", "confirmado")
        finally:
            bloqueador.close()

        self.assertEqual(
            self.c.execute(
                """
                SELECT COUNT(*) FROM lote_hist
                WHERE clave=? AND estado='local_ok'
                """,
                (clave,),
            ).fetchone()[0],
            1,
        )


class LocksConcurrentes(BaseConcurrencia):

    def test_19_lock_se_libera_tras_excepcion(self):
        """Previene dejar worker.lock tras un fallo ordinario de INICIAR."""
        with self.assertRaises(RuntimeError):
            with q.Lock():
                raise RuntimeError("caida simulada")

        self.assertFalse(q.Lock.path.exists())

    def test_20_lock_de_proceso_muerto_se_recupera(self):
        """Previene que un PID muerto impida reiniciar INICIAR."""
        q.Lock.path.write_text("99999999 " + q.now(), encoding="utf-8")

        with patch.object(q, "pid_alive", return_value=False):
            with q.Lock():
                self.assertTrue(q.Lock.path.exists())

        self.assertFalse(q.Lock.path.exists())

    def test_21_lock_de_otro_proceso_vivo_se_respeta(self):
        """Previene que INICIAR sustituya el lock de otro trabajador activo."""
        contenido = "45678 " + q.now()
        q.Lock.path.write_text(contenido, encoding="utf-8")

        with patch.object(q, "pid_alive", return_value=True):
            with self.assertRaises(SystemExit):
                with q.Lock():
                    pass

        self.assertEqual(
            q.Lock.path.read_text(encoding="utf-8"),
            contenido,
        )


    # BUG: Lock.__exit__ elimina el fichero sin comprobar propietario.
    # Si otro proceso recupera el lock durante una operación, el antiguo
    # puede borrar el lock nuevo. Arreglo mínimo: guardar un token único
    # al adquirirlo y comparar ese token antes de unlink().
    def test_23_lock_antiguo_no_borra_lock_de_relevo(self):
        """Previene borrar el lock perteneciente a un trabajador nuevo."""
        lock = q.Lock()
        lock.__enter__()
        relevo = "88888 " + q.now()
        q.Lock.path.write_text(relevo, encoding="utf-8")

        lock.__exit__(None, None, None)

        self.assertTrue(q.Lock.path.exists())
        self.assertEqual(q.Lock.path.read_text(encoding="utf-8"), relevo)

    def test_24_latido_no_recrea_directorios_externos(self):
        """Previene que un latido fallido provoque excepciones sin controlar."""
        q.Lock.path = q.STATE / "inexistente" / "worker.lock"
        q.Lock.latido()
        self.assertFalse(q.Lock.path.exists())


class RendimientoConcurrencia(BaseConcurrencia):

    def test_25_consulta_miles_filas_no_crece_desmesuradamente(self):
        """Previene consultas de estado excesivamente lentas con miles de propuestas."""
        filas = [
            (
                "perf-%d" % i,
                "zona:perf",
                "Prueba %d" % i,
                "{}",
                "preparada",
                q.now(),
                q.now(),
            )
            for i in range(3000)
        ]
        self.c.executemany(
            """
            INSERT INTO propuestas
            (huella,area,titulo,datos,estado,creado,actualizado)
            VALUES(?,?,?,?,?,?,?)
            """,
            filas,
        )
        self.c.commit()

        inicio = time.monotonic()
        n = self.c.execute(
            "SELECT COUNT(*) FROM propuestas WHERE estado='preparada'"
        ).fetchone()[0]
        duracion = time.monotonic() - inicio

        self.assertEqual(n, 3000)
        self.assertLess(duracion, 2.0)

    def test_26_hay_nuevo_miles_items_termina(self):
        """Previene que la detección de nuevas ramas se vuelva impracticable."""
        lo = self.lote()

        lid = self.c.execute(
            "INSERT INTO lotes(inicio,estado) VALUES(?,?)",
            (q.now(), "en_curso"),
        ).lastrowid

        filas_ramas = []
        filas_items = []
        for i in range(1200):
            rama = "gpt-qa/perf-%04d" % i
            sha = "%040x" % (i + 1)
            clave = rama + "@" + sha[:12]
            filas_ramas.append(
                (rama, "zona:perf", "", sha, "aprobada")
            )
            filas_items.append(
                (
                    clave, lid, rama, sha, "zona:perf",
                    "[]", "actions_ok", "{}", q.now(), q.now(),
                )
            )

        self.c.executemany(
            """
            INSERT INTO ramas(rama,area,ruta,sha,estado)
            VALUES(?,?,?,?,?)
            """,
            filas_ramas,
        )
        self.c.executemany(
            """
            INSERT INTO lote_items
            (clave,lote_id,rama,sha,area,propuestas,estado,runs,creado,actualizado)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            filas_items,
        )
        self.c.commit()

        inicio = time.monotonic()
        resultado = lo.hay_nuevo()
        duracion = time.monotonic() - inicio

        self.assertFalse(resultado)
        self.assertLess(duracion, 3.0)

    def test_27_concurrencia_lectura_escritura_conserva_todas_las_filas(self):
        """Previene perder registros durante escrituras y consultas simultáneas."""
        total = 120
        comienzo = threading.Event()

        def escribir():
            c = self.conexion(timeout=2)
            try:
                comienzo.wait(timeout=3)
                for i in range(total):
                    c.execute(
                        """
                        INSERT INTO analisis(area,fecha,head,fuente_sha)
                        VALUES(?,?,?,?)
                        """,
                        ("zona:%d" % i, q.today(), "abc", "abc"),
                    )
                    c.commit()
            finally:
                c.close()

        def leer():
            c = self.conexion(timeout=2)
            try:
                comienzo.wait(timeout=3)
                observados = []
                for _ in range(100):
                    observados.append(
                        c.execute(
                            "SELECT COUNT(*) FROM analisis"
                        ).fetchone()[0]
                    )
                return observados
            finally:
                c.close()

        with ThreadPoolExecutor(max_workers=3) as pool:
            fw = pool.submit(escribir)
            fr1 = pool.submit(leer)
            fr2 = pool.submit(leer)
            comienzo.set()
            fw.result(timeout=8)
            r1 = fr1.result(timeout=8)
            r2 = fr2.result(timeout=8)

        self.assertTrue(all(0 <= n <= total for n in r1 + r2))
        self.assertEqual(
            self.c.execute("SELECT COUNT(*) FROM analisis").fetchone()[0],
            total,
        )
        self.assertEqual(
            self.c.execute("PRAGMA integrity_check").fetchone()[0],
            "ok",
        )


if __name__ == "__main__":
    unittest.main()
