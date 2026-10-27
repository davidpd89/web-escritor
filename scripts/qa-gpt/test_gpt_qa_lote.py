import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import os
import sqlite3
import subprocess
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import qa_gpt as q
import qa_lote as lote


SHA = "a" * 40
RAMA = "gpt-qa/prueba-lote"
CLAVE = f"{RAMA}@{SHA[:12]}"
WORKFLOW = lote.GRUPO_WF


class TestQaLote(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="qa-lote-test-")
        self.addCleanup(self.tmp.cleanup)

        self.base = Path(self.tmp.name)
        self.state = self.base / "state"
        self.root = self.base / "repo"
        self.state.mkdir()
        self.root.mkdir()

        self._patch(q, "STATE", self.state)
        self._patch(q, "DB_PATH", self.state / "estado.db")
        self._patch(q, "ROOT", self.root)
        self._patch(q, "WT", self.state / "wt")
        self._patch(q.Lock, "path", self.state / "worker.lock")
        self._patch(lote, "ABORTAR", None)

        self._patch(q, "reparar_perdidas", MagicMock())
        self._patch(q, "git", MagicMock(return_value=""))
        self._patch(q, "estado_prop", self.estado_prop)

        self.c = sqlite3.connect(self.state / "estado.db", timeout=1)
        self.c.row_factory = sqlite3.Row
        self.addCleanup(self.c.close)

        self.c.executescript("""
            CREATE TABLE propuestas (
                id INTEGER PRIMARY KEY,
                huella TEXT UNIQUE,
                area TEXT,
                titulo TEXT,
                datos TEXT,
                estado TEXT,
                veredicto TEXT,
                rama TEXT,
                creado TEXT,
                actualizado TEXT
            );
            CREATE TABLE ramas (
                rama TEXT PRIMARY KEY,
                area TEXT,
                ruta TEXT,
                sha TEXT,
                estado TEXT,
                pr INTEGER,
                url TEXT
            );
        """)
        lote.migrar(self.c)
        self.c.commit()

        self._patch(q, "db", lambda: self._connection())

        self.gh = MagicMock()
        self.gh.ok.return_value = True
        self.gh.scopes.return_value = {"repo", "workflow"}
        self.gh.remote_sha.return_value = SHA
        self.gh.runs_grupo.return_value = []
        self.gh.runs.return_value = []
        self.gh.workflow_ref.return_value = "automation/qa-gpt"

        self.lo = lote.Lote(
            q,
            gh=self.gh,
            runner=MagicMock(return_value=(0, "")),
            sleep=lambda _: None,
            out=lambda _: None,
            cfg={
                "node_modules": str(self.base / "node_modules"),
                "poll_s": 0,
                "reintentos_infra": 3,
                "tam_lote": 40,
                "panel": False,
            },
        )
        self.addCleanup(self.lo.c.close)

    def test_registrar_test_reintenta_si_la_base_esta_bloqueada(self):
        """Un 'database is locked' al registrar un test no debe tumbar EJECUTAR (2026-10-26): se reintenta como en `set`."""
        self.lo.c.execute("PRAGMA busy_timeout=1")
        otro = sqlite3.connect(self.state / "estado.db", isolation_level=None)
        self.addCleanup(otro.close)
        otro.execute("BEGIN IMMEDIATE")

        def sleep(_):
            if otro.in_transaction: otro.execute("COMMIT")
        self.lo.sleep = sleep
        self.lo.registrar_test(CLAVE, "local", "t.py", "cat", "ok", 0)
        n = self.c.execute("SELECT COUNT(*) FROM lote_tests WHERE clave=?", (CLAVE,)).fetchone()[0]
        self.assertEqual(n, 1)

    def _patch(self, obj, name, value):
        p = patch.object(obj, name, value)
        p.start()
        self.addCleanup(p.stop)

    def _connection(self):
        c = sqlite3.connect(self.state / "estado.db", timeout=1)
        c.row_factory = sqlite3.Row
        return c

    def estado_prop(self, c, pid, estado, detalle="", **kwargs):
        c.execute(
            "UPDATE propuestas SET estado=? WHERE id=?",
            (estado, pid),
        )

    def propuesta(self, pid=1, rama=RAMA, categoria="regresion",
                  estado="preparada", datos=None):
        if datos is None:
            datos = {
                "categoria": categoria,
                "ficheros_nuevos": [
                    {"ruta": "tests/test_prueba.py"}
                ],
                "pasos": [
                    {"argv": ["python", "tests/test_prueba.py"]}
                ],
            }

        self.c.execute(
            """
            INSERT INTO propuestas
                (id, huella, area, titulo, datos, estado, rama)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pid,
                f"huella-{pid}",
                "rendimiento-red",
                f"Prueba {pid}",
                json.dumps(datos),
                estado,
                rama,
            ),
        )
        self.c.commit()

    def rama(self, rama=RAMA, sha=SHA, estado="preparada"):
        self.c.execute(
            """
            INSERT INTO ramas(rama, area, ruta, sha, estado)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rama, "rendimiento-red", "tests", sha, estado),
        )
        self.c.commit()

    def item(self, estado="preparada", clave=CLAVE, rama=RAMA,
             sha=SHA, lid=None, propuestas=None, workflows=None,
             runs=None, intentos=0, local_clase=None, local_log=None):
        if lid is None:
            lid = self.c.execute(
                """
                INSERT INTO lotes(inicio, estado)
                VALUES (?, 'en_curso')
                """,
                (q.now(),),
            ).lastrowid

        self.c.execute(
            """
            INSERT INTO lote_items
                (clave, lote_id, rama, sha, area, propuestas,
                 estado, runs, workflows, intentos, local_clase,
                 local_log, creado, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clave,
                lid,
                rama,
                sha,
                "rendimiento-red",
                json.dumps(propuestas if propuestas is not None else [1]),
                estado,
                json.dumps(runs if runs is not None else {}),
                json.dumps(workflows if workflows is not None else [WORKFLOW]),
                intentos,
                local_clase,
                local_log,
                q.now(),
                q.now(),
            ),
        )
        self.c.commit()
        return self.lo.item(clave)

    def run_remoto(self, rid=123, status="completed",
                   conclusion="success"):
        return {
            "databaseId": rid,
            "headSha": SHA,
            "status": status,
            "conclusion": conclusion,
            "url": f"https://github.com/example/actions/runs/{rid}",
        }

    def test_captura_no_duplica_al_reanudar(self):
        """Evita duplicar tests y autorizaciones al reiniciar EJECUTAR."""
        self.rama()
        self.propuesta()

        primero = self.lo.abrir_lote()
        segundo = self.lo.abrir_lote()

        self.assertEqual(primero, segundo)
        self.assertEqual(
            self.c.execute("SELECT COUNT(*) FROM lote_items").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.c.execute("SELECT COUNT(*) FROM lotes").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.c.execute(
                "SELECT estado FROM propuestas WHERE id=1"
            ).fetchone()[0],
            "aprobada",
        )

    def test_reanudacion_captura_trabajo_generado_despues(self):
        """Evita que INICIAR deje trabajo nuevo fuera de un lote abierto."""
        self.rama()
        self.propuesta()

        lid = self.lo.abrir_lote()

        otra_rama = "gpt-qa/segunda"
        otro_sha = "b" * 40
        self.rama(otra_rama, otro_sha)
        self.propuesta(2, otra_rama)

        self.assertTrue(self.lo.hay_nuevo())
        self.assertEqual(self.lo.abrir_lote(), lid)

        filas = self.lo.items(lid)
        self.assertEqual(len(filas), 2)
        self.assertEqual(len({f["clave"] for f in filas}), 2)
        self.assertFalse(self.lo.hay_nuevo())

    def test_captura_respeta_limite_sin_perder_pendientes(self):
        """Evita lotes ilimitados y pérdida de ramas cuando INICIAR produce más."""
        for i in range(12):
            rama = f"gpt-qa/lote-{i:03d}"
            self.rama(rama, f"{i + 1:040x}")
            self.propuesta(i + 1, rama)

        self.lo.cfg["tam_lote"] = 5
        lid = self.lo.abrir_lote()

        self.assertEqual(len(self.lo.items(lid)), 5)
        self.assertTrue(self.lo.hay_nuevo())

        pendientes = self.c.execute(
            "SELECT COUNT(*) FROM propuestas WHERE estado='preparada'"
        ).fetchone()[0]
        self.assertEqual(pendientes, 7)

    def test_rama_sin_propuestas_no_entra_en_lote(self):
        """Evita ejecutar ramas incompletas por escrituras parciales del worker."""
        self.rama()

        lid = self.lo.abrir_lote()

        self.assertEqual(self.lo.items(lid), [])
        self.assertFalse(self.lo.hay_nuevo())

    def test_reparacion_fallida_no_impide_capturar(self):
        """Evita bloquear EJECUTAR si falla la reparación de ramas perdidas."""
        self.rama()
        self.propuesta()
        q.reparar_perdidas.side_effect = sqlite3.OperationalError(
            "database is locked"
        )

        lid = self.lo.abrir_lote()

        self.assertEqual(len(self.lo.items(lid)), 1)

    def test_lote_cerrado_no_se_reabre_tras_reinicio(self):
        """Evita reutilizar un lote terminado al arrancar otra ejecución."""
        self.rama()
        self.propuesta()

        primero = self.lo.abrir_lote()
        self.lo.set(CLAVE, "actions_ok")

        with patch.object(self.lo, "cerrar_propuestas"):
            self.assertTrue(self.lo.cerrar_lote(primero))

        segundo = self.lo.abrir_lote()

        self.assertNotEqual(primero, segundo)
        self.assertEqual(self.lo.items(segundo), [])

    def test_reintentos_infra_tienen_tope(self):
        """Evita reintentos infinitos cuando la infraestructura falla siempre."""
        self.propuesta()
        self.item(
            estado="infra",
            intentos=3,
            local_clase="infra",
            local_log="fallo anterior",
        )

        self.lo.reintentar_infra([self.lo.item(CLAVE)])

        actual = self.lo.item(CLAVE)
        self.assertEqual(actual["estado"], "fallo_test")
        self.assertIn("persistente", actual["detalle"])

        historial = self.c.execute(
            "SELECT COUNT(*) FROM lote_hist WHERE clave=?",
            (CLAVE,),
        ).fetchone()[0]

        self.lo.reintentar_infra([self.lo.item(CLAVE)])

        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM lote_hist WHERE clave=?",
                (CLAVE,),
            ).fetchone()[0],
            historial,
        )

    def test_reintento_local_no_reenvia_test_sin_validar(self):
        """Evita enviar a Actions un test cuya validación local falló por infraestructura."""
        self.propuesta()
        self.item(
            estado="infra",
            intentos=1,
            local_clase="infra",
            local_log="fallo local",
        )

        self.lo.reintentar_infra([self.lo.item(CLAVE)])

        self.assertEqual(self.lo.item(CLAVE)["estado"], "preparada")
        self.gh.dispatch.assert_not_called()

    def test_envio_reutiliza_run_existente(self):
        """Evita duplicar workflows al caer EJECUTAR después del dispatch."""
        self.propuesta()
        self.item(estado="local_ok", workflows=[WORKFLOW])

        self.gh.runs_grupo.return_value = [self.run_remoto()]

        self.lo.enviar(self.lo.item(CLAVE))

        actual = self.lo.item(CLAVE)
        self.assertEqual(actual["estado"], "actions_pendiente")
        self.assertEqual(
            json.loads(actual["runs"])[WORKFLOW]["id"],
            123,
        )
        self.gh.dispatch.assert_not_called()
        self.gh.push.assert_not_called()

    def test_dispatch_sin_run_localizado_no_se_repite_indefinidamente(self):
        """Evita un sondeo infinito cuando GitHub tarda en publicar el run."""
        self.propuesta()
        self.item(estado="local_ok", workflows=[WORKFLOW])

        self.lo.enviar(self.lo.item(CLAVE))

        self.gh.dispatch.assert_called_once()
        self.assertEqual(self.gh.runs_grupo.call_count, 13)
        self.assertEqual(self.lo.item(CLAVE)["estado"], "enviado")

    def test_reconciliacion_recupera_run_tras_caida(self):
        """Evita perder un run remoto enviado antes de persistir su identificador."""
        self.propuesta()
        self.item(
            estado="enviado",
            workflows=[WORKFLOW],
            runs={},
        )

        self.gh.runs_grupo.return_value = [
            self.run_remoto(status="in_progress", conclusion=None)
        ]
        self.gh.run.return_value = self.run_remoto(
            status="in_progress",
            conclusion=None,
        )

        resultado = self.lo.reconciliar(self.lo.item(CLAVE))

        self.assertEqual(resultado, "viva")
        self.assertEqual(
            self.lo.item(CLAVE)["estado"],
            "actions_ejecutando",
        )
        self.assertEqual(
            json.loads(self.lo.item(CLAVE)["runs"])[WORKFLOW]["id"],
            123,
        )
        self.gh.dispatch.assert_not_called()

    def test_error_de_red_no_convierte_run_en_fallo_de_test(self):
        """Evita falsos fallos de producto durante una interrupción de GitHub."""
        self.propuesta()
        self.item(
            estado="actions_ejecutando",
            runs={
                WORKFLOW: {
                    "id": 123,
                    "url": "https://github.com/example/actions/runs/123",
                }
            },
        )

        self.gh.run.side_effect = lote.GhError("HTTP 502")

        resultado = self.lo.reconciliar(self.lo.item(CLAVE))

        self.assertTrue(resultado.startswith("gh:"))
        self.assertEqual(
            self.lo.item(CLAVE)["estado"],
            "actions_ejecutando",
        )

    def test_token_sin_permisos_no_se_reintenta_como_red(self):
        """Evita repetir envíos que GitHub rechaza por permisos insuficientes."""
        self.propuesta()
        self.item(estado="local_ok")

        self.gh.remote_sha.return_value = None
        self.gh.push.side_effect = lote.GhAuthError(
            "Resource not accessible by integration"
        )

        self.lo.enviar(self.lo.item(CLAVE))

        self.assertEqual(
            self.lo.item(CLAVE)["estado"],
            "revision_humana",
        )
        self.gh.dispatch.assert_not_called()

    def test_no_empuja_ramas_fuera_del_espacio_qa(self):
        """Evita modificar main u otras ramas mediante la fachada de GitHub."""
        gh = lote.Gh(q)

        with self.assertRaises(lote.GhAuthError):
            gh.push(SHA, "main")

        with self.assertRaises(lote.GhAuthError):
            gh.push(SHA, "release/produccion")

    def test_run_cmd_aborta_y_mata_proceso(self):
        """Evita dejar procesos de tests vivos después de pulsar Q."""
        proceso = MagicMock()
        proceso.pid = 98765
        proceso.communicate.side_effect = [
            subprocess.TimeoutExpired("python", 1),
            ("", None),
        ]

        with (
            patch.object(lote.cob, "popen", return_value=proceso),
            patch.object(lote, "ABORTAR", lambda: True),
            patch.object(lote, "matar_arbol") as matar,
        ):
            rc, salida = lote.run_cmd(
                [sys.executable, "test_falso.py"],
                self.root,
                timeout=10,
            )

        self.assertEqual(rc, lote.RC_ABORTADO)
        self.assertIn("ABORTADO", salida)
        matar.assert_called_once_with(proceso)

    def test_validacion_interrumpida_vuelve_a_preparada(self):
        """Evita clasificar una parada voluntaria como fallo del test."""
        self.propuesta()
        self.item(estado="preparada")

        self.lo.parando = "tecla Q"

        wt = self.state / "lote_wt" / self.lo.slug(CLAVE)
        fichero = wt / "tests" / "test_prueba.py"

        def crear_worktree(*args, **kwargs):
            if args[:2] == ("worktree", "add"):
                fichero.parent.mkdir(parents=True, exist_ok=True)
                fichero.write_text(
                    "import unittest\n",
                    encoding="utf-8",
                )
            return ""

        with (
            patch.object(self.lo, "git", side_effect=crear_worktree),
            patch.object(self.lo, "main_sha", return_value="b" * 40),
            patch.object(self.lo, "verificar_rama", return_value=None),
            patch.object(self.lo, "cableado", return_value=[WORKFLOW]),
            patch.object(self.lo, "precheck", return_value=(0, "")),
            patch.object(
                self.lo,
                "ejecutar_test",
                return_value=(lote.RC_ABORTADO, "ABORTADO"),
            ),
            patch.object(self.lo, "limpiar_wt"),
            patch.object(lote.cob, "run", return_value=SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="",
            )),
        ):
            self.lo.validar_local(self.lo.item(CLAVE))

        actual = self.lo.item(CLAVE)
        self.assertEqual(actual["estado"], "preparada")
        self.assertEqual(actual["intentos"], 0)
        self.gh.dispatch.assert_not_called()

    def test_worktree_se_limpia_si_falla_el_test(self):
        """Evita acumular worktrees cuando falla una ejecución local."""
        self.propuesta()
        self.item()

        wt = self.state / "lote_wt" / self.lo.slug(CLAVE)
        fichero = wt / "tests" / "test_prueba.py"

        def crear_worktree(*args, **kwargs):
            if args[:2] == ("worktree", "add"):
                fichero.parent.mkdir(parents=True, exist_ok=True)
                fichero.write_text(
                    "import unittest\n",
                    encoding="utf-8",
                )
            return ""

        with (
            patch.object(self.lo, "git", side_effect=crear_worktree),
            patch.object(self.lo, "main_sha", return_value="b" * 40),
            patch.object(self.lo, "verificar_rama", return_value=None),
            patch.object(self.lo, "cableado", return_value=[WORKFLOW]),
            patch.object(
                self.lo,
                "ejecutar_test",
                side_effect=OSError("proceso no disponible"),
            ),
            patch.object(self.lo, "limpiar_wt") as limpiar,
            patch.object(lote.cob, "run", return_value=SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="",
            )),
        ):
            with self.assertRaises(OSError):
                self.lo.validar_local(self.lo.item(CLAVE))

        limpiar.assert_any_call(wt)

    def test_log_persiste_y_sigue_si_el_disco_falla(self):
        """Evita perder el diagnóstico del flujo PR o tumbarlo por errores de log."""
        mensajes = []
        self.lo.out = mensajes.append

        self.lo.log("Flujo PR: comprobacion inicial")

        log = self.lo.dir / "ejecutar.log"
        self.assertTrue(log.exists())
        self.assertIn(
            "Flujo PR: comprobacion inicial",
            log.read_text(encoding="utf-8"),
        )

        original_open = Path.open

        def fallo_log(path, *args, **kwargs):
            if Path(path) == log:
                raise OSError("disco lleno")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", fallo_log):
            self.lo.log("Flujo PR: disco lleno")

        self.assertTrue(
            any("disco lleno" in mensaje for mensaje in mensajes)
        )

    def test_vigia_avisa_una_sola_vez_por_paso(self):
        """Evita horas de bloqueo silencioso y registros repetidos del mismo paso."""
        avisos = []
        self.lo.log = avisos.append

        hilo = threading.current_thread()
        inicio = time.time() - 3600

        self.assertTrue(self.lo.vigia_paso(hilo, inicio, 1800))
        self.assertFalse(self.lo.vigia_paso(hilo, inicio, 1800))

        self.assertEqual(len(avisos), 1)
        self.assertIn("Flujo PR", avisos[0])
        self.assertIn("pila:", avisos[0])

    def test_lock_rechaza_segunda_ventana_activa(self):
        """Evita que dos EJECUTAR envíen simultáneamente el mismo lote."""
        lock = self.state / "lote.lock"
        lock.write_text("98765 2026-10-26T08:00:00")

        with patch.object(q, "pid_alive", return_value=True):
            with self.assertRaises(SystemExit):
                with lote.LoteLock(q):
                    self.fail("No debe adquirirse un lock activo")

        self.assertTrue(lock.exists())
        self.assertEqual(lock.read_text().split()[0], "98765")

    def test_lock_recupera_pid_muerto_y_libera_al_salir(self):
        """Evita bloquear EJECUTAR para siempre tras una caída del proceso."""
        lock = self.state / "lote.lock"
        lock.write_text("98765 2026-10-26T08:00:00")

        with patch.object(q, "pid_alive", return_value=False):
            with lote.LoteLock(q):
                self.assertEqual(
                    int(lock.read_text().split()[0]),
                    os.getpid(),
                )

        self.assertFalse(lock.exists())

    def test_consulta_de_items_escala_con_miles_de_filas(self):
        """Evita una degradación extrema al recuperar lotes históricos grandes."""
        lid = self.c.execute(
            """
            INSERT INTO lotes(inicio, estado)
            VALUES (?, 'en_curso')
            """,
            (q.now(),),
        ).lastrowid

        filas = [
            (
                f"gpt-qa/carga-{i:05d}@{i:012x}",
                lid,
                f"gpt-qa/carga-{i:05d}",
                f"{i:040x}",
                "rendimiento-red",
                "[]",
                "actions_ok",
                "{}",
                q.now(),
                q.now(),
            )
            for i in range(3000)
        ]

        self.c.executemany(
            """
            INSERT INTO lote_items
                (clave, lote_id, rama, sha, area, propuestas,
                 estado, runs, creado, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            filas,
        )
        self.c.commit()

        inicio = time.monotonic()
        resultado = self.lo.items(lid)
        duracion = time.monotonic() - inicio

        self.assertEqual(len(resultado), 3000)
        self.assertLess(duracion, 5.0)

    def test_resultados_remotos_no_confunden_hallazgo_con_exito(self):
        """Evita marcar como aprobado un defecto demostrado por Actions."""
        self.propuesta(categoria="descubre_defecto")
        self.item(
            estado="actions_ejecutando",
            runs={
                WORKFLOW: {
                    "id": 123,
                    "url": "https://github.com/example/actions/runs/123",
                }
            },
        )

        self.gh.run.return_value = self.run_remoto()
        self.gh.resultados.return_value = {
            "tests": [
                {
                    "ruta": "tests/test_prueba.py",
                    "clase": "hallazgo",
                    "rc": 1,
                }
            ],
            "resumen": {"hallazgo": 1},
        }

        resultado = self.lo.reconciliar(self.lo.item(CLAVE))

        self.assertEqual(resultado, "fin")
        self.assertEqual(
            self.lo.item(CLAVE)["estado"],
            "defecto_demostrado",
        )

        registrado = self.c.execute(
            """
            SELECT clase, rc, run_id
            FROM lote_tests
            WHERE clave=? AND fuente='actions'
            """,
            (CLAVE,),
        ).fetchone()

        self.assertIsNotNone(registrado)
        self.assertEqual(registrado["clase"], "hallazgo")
        self.assertEqual(registrado["rc"], 1)
        self.assertEqual(registrado["run_id"], 123)

    def test_workflow_sin_ejecucion_real_no_se_considera_cableado(self):
        """Evita dar por válido un test solo porque aparece en paths o comentarios."""
        ruta = "tests/test_nueva_regresion.py"

        textos = {
            "falso.yml": """
name: falso
on:
  workflow_dispatch:
  push:
    paths:
      - tests/test_nueva_regresion.py
jobs:
  comprobar:
    runs-on: ubuntu-latest
    steps:
      - run: echo "No ejecuto el test"
""",
            "real.yml": """
name: real
on:
  workflow_dispatch:
jobs:
  comprobar:
    runs-on: ubuntu-latest
    steps:
      - run: python tests/test_nueva_regresion.py
""",
        }

        encontrados = lote.workflows_que_ejecutan(
            [ruta],
            textos,
            preferidos=("real.yml",),
        )

        self.assertEqual(encontrados, ["real.yml"])


if __name__ == "__main__":
    unittest.main()
