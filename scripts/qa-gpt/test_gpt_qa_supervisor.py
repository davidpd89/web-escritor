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
from unittest.mock import MagicMock, patch

import qa_gpt as q
import qa_supervisor as S


TB = """Traceback (most recent call last):
  File "C:\\GIT\\web-escritor-qa-gpt\\scripts\\qa-gpt\\qa_gpt.py", line 173, in area_stats
    raise RuntimeError("fallo")
RuntimeError: fallo
"""


class Base(unittest.TestCase):
    def setUp(self):
        originales = {
            "STATE": q.STATE,
            "DB_PATH": q.DB_PATH,
            "ROOT": q.ROOT,
            "WT": q.WT,
            "LOCK": q.Lock.path,
            "REPO_QA": S.REPO_QA,
            "CFG": q.CFG,
        }

        def restaurar():
            q.STATE = originales["STATE"]
            q.DB_PATH = originales["DB_PATH"]
            q.ROOT = originales["ROOT"]
            q.WT = originales["WT"]
            q.Lock.path = originales["LOCK"]
            S.REPO_QA = originales["REPO_QA"]
            q.CFG = originales["CFG"]

        self.addCleanup(restaurar)

        self.tmp = tempfile.TemporaryDirectory(
            ignore_cleanup_errors=True
        )
        self.addCleanup(self.tmp.cleanup)

        self.base = Path(self.tmp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()

        q.STATE = self.base / "state"
        q.STATE.mkdir()
        q.DB_PATH = q.STATE / "e.db"
        q.Lock.path = q.STATE / "worker.lock"
        q.ROOT = self.repo
        q.WT = q.STATE / "wt"
        q.CFG = dict(originales["CFG"])

        S.REPO_QA = self.repo

        self.salidas = []
        self.claude_llamadas = []

    def supervisor(self, run=None, claude=None):
        def claude_falso(clave, sistema, entrada, herramientas, cwd):
            self.claude_llamadas.append(
                (clave, sistema, entrada, herramientas, Path(cwd))
            )
            return {
                "resultado": "no_se_puede",
                "causa": "incidente simulado",
                "resumen": "sin cambios",
            }

        return S.Supervisor(
            q,
            out=self.salidas.append,
            run=run or (lambda cmd, cwd, timeout=600: (0, "")),
            claude=claude or claude_falso,
        )

    def registro(self, datos):
        ruta = q.STATE / "supervisor" / "reparaciones.json"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(datos), encoding="utf-8")
        return ruta

    def crear_bd_atasco(self):
        conexion = sqlite3.connect(q.DB_PATH)
        conexion.executescript("""
            CREATE TABLE eventos (
                fecha TEXT
            );
            CREATE TABLE jobs (
                estado TEXT,
                actualizado TEXT,
                no_antes TEXT
            );
            CREATE TABLE triaje (
                pr_estado TEXT
            );
        """)
        conexion.commit()
        conexion.close()

        original = q.db

        def conectar():
            return sqlite3.connect(q.DB_PATH)

        q.db = conectar
        self.addCleanup(lambda: setattr(q, "db", original))

    def crear_entrada(self, carpeta, nombre, edad_horas=8, contenido="x"):
        directorio = q.STATE / carpeta
        directorio.mkdir(parents=True, exist_ok=True)

        archivo = directorio / nombre
        archivo.write_text(contenido, encoding="utf-8")

        fecha = time.time() - edad_horas * 3600
        os.utime(archivo, (fecha, fecha))
        return archivo


class FirmaYRegistro(Base):
    def test_firma_estable_ante_cambios_de_linea(self):
        """Evita repetir una reparación porque cambió el número de línea del traceback."""
        primero = S.firma(TB)
        segundo = S.firma(
            TB.replace("line 173", "line 9999")
        )

        self.assertEqual(primero, segundo)
        self.assertEqual(
            primero,
            "RuntimeError@qa_gpt.py:area_stats",
        )

    def test_traceback_elige_ultima_caida(self):
        """Evita reparar un traceback antiguo cuando el log contiene varias caídas."""
        texto = (
            TB
            + "\nProceso relanzado\n"
            + TB.replace("RuntimeError", "ValueError")
        )

        ultimo = S.traceback_de(texto)

        self.assertEqual(
            S.firma(ultimo),
            "ValueError@qa_gpt.py:area_stats",
        )
        self.assertEqual(
            ultimo.count("Traceback (most recent call last):"),
            1,
        )

    def test_registro_json_corrupto_no_impide_arrancar(self):
        """Evita que un registro de reparaciones truncado tumbe el supervisor."""
        s = self.supervisor()
        ruta = self.registro({})
        ruta.write_text('{"fallo":', encoding="utf-8")

        self.assertEqual(s._registro(), {})
        self.assertTrue(s.permitido("nuevo:fallo"))

    def test_firma_repetida_y_tope_diario(self):
        """Evita reparaciones ilimitadas de una firma o de fallos distintos durante el día."""
        s = self.supervisor()
        s.cfg["max_reparaciones_dia"] = 2

        hoy = q.today()
        self.registro({
            "fallo:a": hoy + "T08:00:00",
            "fallo:b": hoy + "T08:01:00",
        })

        self.assertFalse(s.permitido("fallo:a"))
        self.assertFalse(s.permitido("fallo:c"))

        s.cfg["max_reparaciones_dia"] = 3
        self.assertTrue(s.permitido("fallo:c"))

    def test_main_rojo_reintenta_tras_una_hora_y_tres_intentos(self):
        """Evita abandonar main en rojo tras un intento fallido o reintentarlo sin límite."""
        s = self.supervisor()
        ahora = dt.datetime.fromisoformat(q.now()[:19])
        firma = "main-rojo:40227985780"

        reciente = (ahora - dt.timedelta(minutes=30)).isoformat()
        antiguo = (ahora - dt.timedelta(hours=2)).isoformat()

        self.registro({firma: f"{reciente} error 1"})
        self.assertFalse(s.permitido(firma))

        self.registro({firma: f"{antiguo} error 1"})
        self.assertTrue(s.permitido(firma))

        self.registro({firma: f"{antiguo} error 3"})
        self.assertFalse(s.permitido(firma))

        self.registro({firma: f"{antiguo} pr_abierta 1"})
        self.assertFalse(s.permitido(firma))

    def test_anotar_persiste_aunque_falle_evento_bd(self):
        """Evita perder el historial del incidente por un error secundario de SQLite."""
        s = self.supervisor()

        with patch.object(
            q,
            "db",
            side_effect=sqlite3.OperationalError("database is locked"),
        ):
            s.anotar(
                "fallo:disco",
                "error",
                "SQLite ocupado durante el registro",
            )

        registro = s._registro()
        historial = s.dir / "historial.log"

        self.assertIn("fallo:disco", registro)
        self.assertTrue(historial.exists())
        self.assertIn(
            "SQLite ocupado",
            historial.read_text(encoding="utf-8"),
        )


class Atascos(Base):
    def test_esperas_legitimas_no_disparan_reparacion(self):
        """Evita llamar a Claude durante pausas manuales, login o límites de uso."""
        s = self.supervisor()
        servicio = q.STATE / "servicio.json"

        for estado in S.Supervisor.ESPERAS_LEGITIMAS:
            with self.subTest(estado=estado):
                servicio.write_text(
                    json.dumps({"estado": estado}),
                    encoding="utf-8",
                )

                with patch.object(
                    q,
                    "db",
                    side_effect=AssertionError(
                        "No debe consultar la BD durante una pausa"
                    ),
                ):
                    self.assertIsNone(s.atasco())

    def test_servicio_json_malformado_no_oculta_atasco(self):
        """Evita que servicio.json truncado desactive permanentemente la vigilancia."""
        self.crear_bd_atasco()
        s = self.supervisor()
        s.cfg["atasco_min"] = 20

        antiguo = (
            dt.datetime.fromisoformat(q.now()[:19])
            - dt.timedelta(minutes=45)
        ).isoformat()

        with sqlite3.connect(q.DB_PATH) as c:
            c.execute(
                "INSERT INTO eventos(fecha) VALUES (?)",
                (antiguo,),
            )
            c.execute(
                "INSERT INTO jobs(estado, actualizado, no_antes) "
                "VALUES (?, ?, ?)",
                ("pendiente", antiguo, ""),
            )

        (q.STATE / "servicio.json").write_text(
            '{"estado":',
            encoding="utf-8",
        )

        descripcion = s.atasco()

        self.assertIsNotNone(descripcion)
        self.assertIn("sin actividad", descripcion)

    def test_no_hay_atasco_si_trabajo_es_futuro(self):
        """Evita reparar un pipeline que espera legítimamente la fecha no_antes."""
        self.crear_bd_atasco()
        s = self.supervisor()

        ahora = dt.datetime.fromisoformat(q.now()[:19])
        antiguo = (ahora - dt.timedelta(hours=2)).isoformat()
        futuro = (ahora + dt.timedelta(hours=3)).isoformat()

        with sqlite3.connect(q.DB_PATH) as c:
            c.execute(
                "INSERT INTO eventos(fecha) VALUES (?)",
                (antiguo,),
            )
            c.execute(
                "INSERT INTO jobs(estado, actualizado, no_antes) "
                "VALUES (?, ?, ?)",
                ("pendiente", antiguo, futuro),
            )

        self.assertIsNone(s.atasco())

    def test_job_en_curso_antiguo_si_es_atasco(self):
        """Evita dejar indefinidamente un job en_curso sin actividad real."""
        self.crear_bd_atasco()
        s = self.supervisor()
        s.cfg["atasco_min"] = 20

        antiguo = (
            dt.datetime.fromisoformat(q.now()[:19])
            - dt.timedelta(minutes=60)
        ).isoformat()

        with sqlite3.connect(q.DB_PATH) as c:
            c.execute(
                "INSERT INTO jobs(estado, actualizado, no_antes) "
                "VALUES (?, ?, ?)",
                ("en_curso", antiguo, None),
            )

        descripcion = s.atasco()

        self.assertIsNotNone(descripcion)
        self.assertIn("1 jobs ejecutables", descripcion)

    def test_miles_de_jobs_no_provocan_consultas_por_fila(self):
        """Evita que la vigilancia se degrade con miles de jobs acumulados."""
        self.crear_bd_atasco()
        s = self.supervisor()

        antiguo = (
            dt.datetime.fromisoformat(q.now()[:19])
            - dt.timedelta(hours=2)
        ).isoformat()

        with sqlite3.connect(q.DB_PATH) as c:
            c.executemany(
                "INSERT INTO jobs(estado, actualizado, no_antes) "
                "VALUES (?, ?, ?)",
                [
                    ("terminado", antiguo, None)
                    for _ in range(10000)
                ],
            )
            c.execute(
                "INSERT INTO jobs(estado, actualizado, no_antes) "
                "VALUES (?, ?, ?)",
                ("en_curso", antiguo, None),
            )

        inicio = time.monotonic()
        descripcion = s.atasco()
        duracion = time.monotonic() - inicio

        self.assertIn("1 jobs ejecutables", descripcion)
        self.assertLess(duracion, 3.0)

    def test_flujo_pr_parado_solo_si_ejecutar_sigue_vivo(self):
        """Detecta el hilo PR congelado sin confundirlo con EJECUTAR detenido."""
        s = self.supervisor()
        s.cfg["flujo_pr_min"] = 90

        lote = q.STATE / "lote"
        lote.mkdir()

        ejecutar = lote / "ejecutar.log"
        ciclo = lote / "ciclo.json"

        ejecutar.write_text("activo\n", encoding="utf-8")
        ciclo.write_text("{}", encoding="utf-8")

        ahora = time.time()
        os.utime(ejecutar, (ahora, ahora))
        os.utime(ciclo, (ahora - 3 * 3600, ahora - 3 * 3600))

        self.assertIn(
            "flujo PR no completa un paso",
            s.flujo_pr_parado(),
        )

        os.utime(
            ejecutar,
            (ahora - 3600, ahora - 3600),
        )

        self.assertIsNone(s.flujo_pr_parado())

    def test_flujo_pr_sin_archivos_no_es_falso_atasco(self):
        """Evita diagnosticar un atasco PR antes de crear ciclo.json y ejecutar.log."""
        s = self.supervisor()

        self.assertIsNone(s.flujo_pr_parado())

        lote = q.STATE / "lote"
        lote.mkdir()
        (lote / "ejecutar.log").write_text(
            "iniciando",
            encoding="utf-8",
        )

        self.assertIsNone(s.flujo_pr_parado())


class Reinicio(Base):
    def test_reinicio_controlado_no_llama_a_claude(self):
        """Evita interpretar el código REINICIO como un fallo reparable."""
        s = self.supervisor()

        respuestas = iter([
            (S.REINICIO, ""),
            (0, ""),
        ])

        s._hijo = lambda args: next(respuestas)
        s.reparar_codigo = MagicMock(
            side_effect=AssertionError("Claude no debe ejecutarse")
        )

        self.assertEqual(s.ejecutar(["iniciar"]), 0)
        s.reparar_codigo.assert_not_called()

    def test_keyboardinterrupt_no_dispara_reparacion(self):
        """Evita reparar el pipeline cuando el usuario lo interrumpe."""
        s = self.supervisor()
        s._hijo = lambda args: (
            1,
            "Traceback (most recent call last):\n"
            "KeyboardInterrupt\n",
        )

        s.reparar_codigo = MagicMock()

        self.assertEqual(s.ejecutar(["iniciar"]), 1)
        s.reparar_codigo.assert_not_called()

    def test_caidas_repetidas_aplican_pausa_anti_bucle(self):
        """Evita un bucle de relanzamientos rápidos cuando la reparación no funciona."""
        s = self.supervisor()

        respuestas = iter(
            [(1, TB)] * 7 + [(0, "")]
        )

        s._hijo = lambda args: next(respuestas)
        s.reparar_codigo = MagicMock(return_value="omitido")
        s.liberar_disco = MagicMock(return_value=0)

        esperas = []

        with patch.object(S.time, "sleep", side_effect=esperas.append):
            resultado = s.ejecutar(["ejecutar-actions"])

        self.assertEqual(resultado, 0)
        self.assertEqual(
            esperas,
            [30, 30, 30, 30, 30, 900, 900],
        )
        self.assertEqual(s.reparar_codigo.call_count, 7)

    def test_fallo_limpieza_disco_no_mata_supervisor(self):
        """Evita que un error de disco impida relanzar EJECUTAR tras una caída."""
        s = self.supervisor()

        respuestas = iter([
            (1, TB),
            (0, ""),
        ])

        s._hijo = lambda args: next(respuestas)
        s.reparar_codigo = MagicMock(return_value="omitido")
        s.liberar_disco = MagicMock(
            side_effect=OSError("disco inaccesible")
        )

        with patch.object(S.time, "sleep", return_value=None):
            resultado = s.ejecutar(["ejecutar-actions"])

        self.assertEqual(resultado, 0)
        self.assertTrue(
            any(
                "limpieza de disco omitida" in salida
                for salida in self.salidas
            )
        )


class Limpieza(Base):
    def test_disco_suficiente_no_toca_worktrees(self):
        """Evita eliminar recursos cuando no existe presión de espacio."""
        llamadas = []

        s = self.supervisor(
            run=lambda cmd, cwd, timeout=600: (
                llamadas.append(cmd) or (0, "")
            )
        )
        s.cfg["disco_min_gb"] = 0

        with patch.object(
            S.shutil,
            "disk_usage",
            return_value=MagicMock(free=100 * 10**9),
        ):
            self.assertEqual(s.liberar_disco(), 0)

        self.assertEqual(llamadas, [])

    def test_disco_conserva_worktree_con_cambios(self):
        """Evita perder trabajo sin commitear al liberar disco."""
        s = self.supervisor(
            run=lambda cmd, cwd, timeout=600: (
                (0, " M archivo.py")
                if cmd[:3] == [
                    "git", "status", "--porcelain"
                ]
                else (0, "")
            )
        )

        viejo = q.STATE / "wt" / "trabajo"
        viejo.mkdir(parents=True)

        fecha = time.time() - 8 * 3600
        os.utime(viejo, (fecha, fecha))

        s.cfg["disco_min_gb"] = 10**9

        with patch.object(
            S.shutil,
            "disk_usage",
            return_value=MagicMock(free=10**9),
        ), patch.object(s, "anotar"):
            borrados = s.liberar_disco()

        self.assertEqual(borrados, 0)
        self.assertTrue(viejo.exists())

    def test_disco_no_borra_worktree_si_git_status_falla(self):
        """Evita destruir trabajo cuando git no puede comprobar si está limpio."""
        comandos = []

        def run(cmd, cwd, timeout=600):
            comandos.append(cmd)
            if cmd[:3] == [
                "git", "status", "--porcelain"
            ]:
                return 128, "fatal: not a git repository"
            return 0, ""

        s = self.supervisor(run=run)

        viejo = q.STATE / "wt" / "desconocido"
        viejo.mkdir(parents=True)
        (viejo / ".git").write_text("gitdir: no-existe\n")  # worktree real; un resto sin .git si se borra

        fecha = time.time() - 8 * 3600
        os.utime(viejo, (fecha, fecha))

        s.cfg["disco_min_gb"] = 10**9

        with patch.object(
            S.shutil,
            "disk_usage",
            return_value=MagicMock(free=10**9),
        ), patch.object(s, "anotar"):
            s.liberar_disco()

        self.assertTrue(
            viejo.exists(),
            "Un fallo de git status no demuestra que el worktree esté limpio",
        )
        self.assertFalse(
            any(
                cmd[:3] == ["git", "worktree", "remove"]
                for cmd in comandos
            ),
            "No debe forzarse la eliminación tras un error de git",
        )

    def test_podar_ci_conserva_versionados_y_recientes(self):
        """Evita borrar informes versionados o recientes al reducir una carpeta .ci."""
        ci = self.repo / ".ci"
        ci.mkdir()

        versionado = self.crear_entrada(
            "informes", "versionado"
        )
        versionado.rename(ci / "versionado")

        reciente = ci / "reciente"
        reciente.write_text("nuevo", encoding="utf-8")

        antiguo = ci / "antiguo"
        antiguo.write_text("viejo", encoding="utf-8")

        hace = time.time() - 4 * 3600
        os.utime(ci / "versionado", (hace, hace))
        os.utime(antiguo, (hace, hace))

        def run(cmd, cwd, timeout=600):
            if cmd[:2] == ["git", "ls-files"]:
                return 0, "versionado\n"
            return 0, ""

        s = self.supervisor(run=run)
        s.cfg["ci_dirs"] = [ci]
        s.cfg["ci_max"] = 0

        borrados = s.podar_ci()

        self.assertEqual(borrados, 1)
        self.assertTrue((ci / "versionado").exists())
        self.assertTrue(reciente.exists())
        self.assertFalse(antiguo.exists())

    def test_podar_ci_no_borra_si_git_ls_files_falla(self):
        """Evita eliminar archivos versionados cuando Git no puede identificarlos."""
        ci = self.repo / ".ci"
        ci.mkdir()

        archivo = ci / "informe"
        archivo.write_text("datos", encoding="utf-8")

        hace = time.time() - 4 * 3600
        os.utime(archivo, (hace, hace))

        s = self.supervisor(
            run=lambda cmd, cwd, timeout=600: (
                128,
                "fatal: git unavailable",
            )
        )

        s.cfg["ci_dirs"] = [ci]
        s.cfg["ci_max"] = 0

        self.assertEqual(s.podar_ci(), 0)
        self.assertTrue(archivo.exists())


if __name__ == "__main__":
    unittest.main()
