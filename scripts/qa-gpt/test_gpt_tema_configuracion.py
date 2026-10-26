import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones offline de configuracion y entorno del pipeline QA-GPT."""

import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest import mock

import qa_gpt as q
import qa_lote
import qa_pr
import qa_supervisor


class ConfiguracionEntorno(unittest.TestCase):
    """Pruebas aisladas de configuracion, herramientas y recuperacion."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

        self.base = Path(self.tmp.name)
        self.root = self.base / "repositorio con espacios y acentos"
        self.root.mkdir()
        self.state = self.base / "estado QA"
        self.state.mkdir()

        for nombre, valor in {
            "ROOT": self.root,
            "STATE": self.state,
            "DB_PATH": self.state / "estado.db",
            "WT": self.state / "wt",
            "SVC": self.state / "servicio.json",
            "AUTORIZ": self.state / "ejecucion_autorizada",
        }.items():
            if hasattr(q, nombre):
                parche = mock.patch.object(q, nombre, valor)
                parche.start()
                self.addCleanup(parche.stop)

        parche_lock = mock.patch.object(
            q.Lock, "path", self.state / "worker.lock"
        )
        parche_lock.start()
        self.addCleanup(parche_lock.stop)

        parche_cfg = mock.patch.object(q, "CFG", dict(q.CFG))
        parche_cfg.start()
        self.addCleanup(parche_cfg.stop)

        self.env_patch = mock.patch.dict(
            os.environ,
            {
                "QA_GPT_SRC": str(self.root),
                "QA_GPT_STATE": str(self.state),
                "LOCALAPPDATA": str(self.base),
            },
        )
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

        self.c = q.db()
        self.addCleanup(self.c.close)

    def supervisor(self, run=None, cfg=None):
        if cfg:
            q.CFG["supervisor"] = cfg
        return qa_supervisor.Supervisor(
            q,
            out=lambda *args: None,
            run=run or (lambda *args, **kwargs: (0, "")),
            claude=lambda *args, **kwargs: {},
        )

    def lote(self, runner=None, cfg=None):
        gh = mock.Mock()
        gh.ok.return_value = True
        obj = qa_lote.Lote(
            q,
            gh=gh,
            runner=runner or (lambda *args, **kwargs: (0, "")),
            sleep=lambda _: None,
            out=lambda *args: None,
            cfg=cfg or {},
        )
        self.addCleanup(obj.c.close)
        return obj

    def test_configuracion_publicada_es_json_valido(self):
        """Evita arrancar con un config.json truncado o sintacticamente invalido."""
        ruta = Path(q.__file__).resolve().parent / "config.json"
        cfg = json.loads(ruta.read_text(encoding="utf-8"))
        self.assertIsInstance(cfg, dict)
        self.assertIsInstance(cfg["areas"], list)
        self.assertTrue(cfg["areas"])

    def test_areas_configuradas_tienen_identificadores_unicos(self):
        """Evita que dos areas compartan identidad y mezclen sus propuestas."""
        areas = q.CFG["areas"]
        ids = [area["id"] for area in areas]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(isinstance(x, str) and x.strip() for x in ids))

    def test_configuracion_sin_opciones_facultativas(self):
        """Evita fallos por ausencia de parametros opcionales del lote."""
        q.CFG.pop("lote", None)
        q.CFG.pop("supervisor", None)

        lo = self.lote()
        su = self.supervisor()

        self.assertGreater(lo.cfg["timeout_test_s"], 0)
        self.assertGreater(lo.cfg["reintentos_infra"], 0)
        self.assertGreater(su.cfg["disco_min_gb"], 0)
        self.assertGreater(su.cfg["vigilar_s"], 0)

    def test_configuracion_parcial_conserva_valores_por_defecto(self):
        """Evita perder los limites de seguridad al sobrescribir una opcion."""
        lo = self.lote(cfg={"poll_s": 7})
        self.assertEqual(lo.cfg["poll_s"], 7)
        self.assertEqual(lo.cfg["timeout_test_s"], 300)
        self.assertEqual(lo.cfg["reintentos_infra"], 3)

    def test_rutas_con_espacios_y_acentos_en_estado(self):
        """Evita escrituras fuera del directorio temporal en rutas Windows."""
        self.assertTrue(str(q.ROOT).endswith("repositorio con espacios y acentos"))
        self.assertEqual(q.DB_PATH.parent, q.STATE)

        q.enqueue(
            self.c,
            "A",
            "zona:configuracion",
            {"motivo": "prueba"},
            "configuracion:espacios",
        )

        fila = self.c.execute(
            "SELECT estado FROM jobs WHERE clave=?",
            ("configuracion:espacios",),
        ).fetchone()

        self.assertIsNotNone(fila)
        self.assertEqual(fila["estado"], "pendiente")
        self.assertTrue(q.DB_PATH.exists())

    def test_db_reabre_con_estado_persistente(self):
        """Evita perder trabajos pendientes al reiniciar el proceso."""
        q.enqueue(
            self.c,
            "A",
            "zona:entorno",
            {"motivo": "persistencia"},
            "configuracion:persistencia",
        )

        otra = q.db()
        try:
            fila = otra.execute(
                "SELECT estado,payload FROM jobs WHERE clave=?",
                ("configuracion:persistencia",),
            ).fetchone()
            self.assertIsNotNone(fila)
            self.assertEqual(fila["estado"], "pendiente")
            self.assertEqual(
                json.loads(fila["payload"])["motivo"],
                "persistencia",
            )
        finally:
            otra.close()

    def test_git_ausente_no_invoca_shell(self):
        """Evita ejecutar comandos mediante shell cuando falta git."""
        with mock.patch(
            "qa_cobertura.run",
            side_effect=FileNotFoundError("git no instalado"),
        ) as ejecutar:
            with self.assertRaises(FileNotFoundError):
                q.sh(["git", "status"])

        ejecutar.assert_called_once()
        self.assertEqual(ejecutar.call_args.args[0], ["git", "status"])
        self.assertEqual(ejecutar.call_args.kwargs["cwd"], self.root)
        self.assertFalse(ejecutar.call_args.kwargs.get("shell", False))

    def test_git_error_devuelve_diagnostico(self):
        """Evita que un git fallido se interprete como operacion correcta."""
        resultado = SimpleNamespace(
            returncode=128,
            stdout="",
            stderr="fatal: not a git repository",
        )

        with mock.patch("qa_cobertura.run", return_value=resultado):
            with self.assertRaisesRegex(RuntimeError, "not a git repository"):
                q.sh(["git", "status"])

    def test_git_check_false_no_oculta_la_salida(self):
        """Evita perder diagnosticos cuando una consulta git es recuperable."""
        resultado = SimpleNamespace(
            returncode=128,
            stdout="estado parcial",
            stderr="fatal",
        )

        with mock.patch("qa_cobertura.run", return_value=resultado):
            salida = q.sh(["git", "status"], check=False)

        self.assertEqual(salida, "estado parcial")

    def test_supervisor_herramienta_ausente(self):
        """Evita que un ejecutable ausente derribe la vigilancia."""
        with mock.patch(
            "qa_cobertura.run",
            side_effect=FileNotFoundError("claude no instalado"),
        ):
            rc, salida = qa_supervisor.Supervisor._run_real(
                ["claude", "--version"],
                self.root,
            )

        self.assertEqual(rc, 127)
        self.assertIn("claude no instalado", salida)

    def test_supervisor_timeout_de_comando(self):
        """Evita que un timeout externo termine la vigilancia completa."""
        with mock.patch(
            "qa_cobertura.run",
            side_effect=subprocess.TimeoutExpired(["git"], 2),
        ):
            rc, salida = qa_supervisor.Supervisor._run_real(
                ["git", "status"],
                self.root,
                timeout=2,
            )

        self.assertEqual(rc, 124)
        self.assertIn("timeout", salida.lower())

    def test_supervisor_registro_corrupto_se_recupera(self):
        """Evita bloquear las reparaciones por un JSON de historial roto."""
        su = self.supervisor()
        ruta = su.dir / "reparaciones.json"
        ruta.write_text('{"incompleto":', encoding="utf-8")

        self.assertEqual(su._registro(), {})
        self.assertTrue(su.permitido("configuracion:json-corrupto"))

    def test_supervisor_registro_ausente(self):
        """Evita que una instalacion nueva necesite historial previo."""
        su = self.supervisor()
        self.assertFalse((su.dir / "reparaciones.json").exists())
        self.assertEqual(su._registro(), {})

    def test_supervisor_limite_diario_de_reparaciones(self):
        """Evita bucles de Claude cuando se repiten errores del entorno."""
        su = self.supervisor(cfg={"max_reparaciones_dia": 2})
        hoy = q.today()

        (su.dir / "reparaciones.json").write_text(
            json.dumps({
                "error:git": hoy + "T09:00:00",
                "error:node": hoy + "T09:01:00",
            }),
            encoding="utf-8",
        )

        self.assertFalse(su.permitido("error:claude"))
        self.assertFalse(su.permitido("error:git"))

    def test_supervisor_incidente_main_rojo_no_agota_cupo_general(self):
        """Evita que un despliegue roto espere al dia siguiente por el cupo."""
        su = self.supervisor(cfg={"max_reparaciones_dia": 0})
        self.assertTrue(su.permitido("main-rojo:run-nuevo"))

    def test_supervisor_main_rojo_con_pr_abierta_no_reintenta(self):
        """Evita crear PR duplicadas para reparar el mismo fallo de main."""
        su = self.supervisor()
        firma = "main-rojo:run-123"

        (su.dir / "reparaciones.json").write_text(
            json.dumps({
                firma: "2026-10-25T08:00:00 pr_abierta 1",
            }),
            encoding="utf-8",
        )

        self.assertFalse(su.permitido(firma))

    def test_supervisor_main_rojo_agota_tres_intentos(self):
        """Evita reintentos ilimitados cuando Claude no consigue reparar main."""
        su = self.supervisor()
        firma = "main-rojo:run-456"

        (su.dir / "reparaciones.json").write_text(
            json.dumps({
                firma: "2026-10-20T08:00:00 error 3",
            }),
            encoding="utf-8",
        )

        self.assertFalse(su.permitido(firma))

    def test_supervisor_sin_espacio_no_borra_trabajo_modificado(self):
        """Evita perder cambios sin confirmar durante la limpieza de disco."""
        wt = self.state / "wt" / "trabajo-pendiente"
        wt.mkdir(parents=True)
        (wt / ".git").write_text("gitdir: temporal", encoding="utf-8")
        (wt / "cambio.py").write_text("x = 1\n", encoding="utf-8")

        viejo = time.time() - 86400
        os.utime(wt, (viejo, viejo))

        comandos = []

        def runner(cmd, cwd, timeout=600, env=None):
            comandos.append(cmd)
            if cmd[:2] == ["git", "status"]:
                return 0, " M cambio.py\n"
            return 0, ""

        su = self.supervisor(
            run=runner,
            cfg={"disco_min_gb": 10**9, "wt_viejo_h": 1},
        )

        with mock.patch(
            "qa_supervisor.shutil.disk_usage",
            return_value=SimpleNamespace(
                total=100,
                used=99,
                free=1,
            ),
        ), mock.patch.object(su, "anotar"):
            borrados = su.liberar_disco()

        self.assertEqual(borrados, 0)
        self.assertTrue((wt / "cambio.py").exists())
        self.assertFalse(any(
            cmd[:3] == ["git", "worktree", "remove"]
            for cmd in comandos
        ))

    def test_supervisor_git_fallido_conserva_worktree(self):
        """Evita borrar worktrees cuando git no puede verificar sus cambios."""
        wt = self.state / "wt" / "rama-bloqueada"
        wt.mkdir(parents=True)
        (wt / ".git").write_text("gitdir: temporal", encoding="utf-8")

        viejo = time.time() - 86400
        os.utime(wt, (viejo, viejo))

        comandos = []

        def runner(cmd, cwd, timeout=600, env=None):
            comandos.append(cmd)
            if cmd[:2] == ["git", "status"]:
                return 127, "git no instalado"
            return 0, ""

        su = self.supervisor(
            run=runner,
            cfg={"disco_min_gb": 10**9, "wt_viejo_h": 1},
        )

        with mock.patch(
            "qa_supervisor.shutil.disk_usage",
            return_value=SimpleNamespace(
                total=100,
                used=99,
                free=1,
            ),
        ), mock.patch.object(su, "anotar"):
            borrados = su.liberar_disco()

        self.assertEqual(borrados, 0)
        self.assertTrue(wt.exists())
        self.assertFalse(any(
            cmd[:3] == ["git", "worktree", "remove"]
            for cmd in comandos
        ))

    def test_supervisor_no_poda_ci_si_git_falla(self):
        """Evita borrar archivos versionados cuando falla su identificacion."""
        ci = self.root / ".ci"
        ci.mkdir()

        for i in range(8):
            p = ci / f"informe-{i}.json"
            p.write_text("{}", encoding="utf-8")
            viejo = time.time() - 86400
            os.utime(p, (viejo, viejo))

        su = self.supervisor(
            run=lambda *args, **kwargs: (127, "git no instalado"),
            cfg={"ci_dirs": [str(ci)], "ci_max": 2},
        )

        self.assertEqual(su.podar_ci(), 0)
        self.assertEqual(len(list(ci.iterdir())), 8)

    def test_supervisor_detecta_flujo_pr_colgado(self):
        """Evita que el hilo de PR permanezca bloqueado toda la noche."""
        lote = self.state / "lote"
        lote.mkdir()

        log = lote / "ejecutar.log"
        ciclo = lote / "ciclo.json"

        log.write_text("EJECUTAR activo", encoding="utf-8")
        ciclo.write_text('{"estado":"en_curso"}', encoding="utf-8")

        ahora = time.time()
        os.utime(log, (ahora, ahora))
        os.utime(ciclo, (ahora - 7200, ahora - 7200))

        su = self.supervisor(cfg={"flujo_pr_min": 90})
        aviso = su.flujo_pr_parado()

        self.assertIsNotNone(aviso)
        self.assertIn("flujo PR", aviso)

    def test_supervisor_no_denuncia_flujo_pr_sin_ejecutar(self):
        """Evita reparaciones innecesarias cuando EJECUTAR ya esta detenido."""
        lote = self.state / "lote"
        lote.mkdir()

        log = lote / "ejecutar.log"
        ciclo = lote / "ciclo.json"

        log.write_text("detenido", encoding="utf-8")
        ciclo.write_text("{}", encoding="utf-8")

        viejo = time.time() - 7200
        os.utime(log, (viejo, viejo))
        os.utime(ciclo, (viejo, viejo))

        su = self.supervisor(cfg={"flujo_pr_min": 30})
        self.assertIsNone(su.flujo_pr_parado())

    def test_lote_lock_de_proceso_muerto_se_recupera(self):
        """Evita bloquear EJECUTAR tras una terminacion inesperada."""
        lock = self.state / "lote.lock"
        lock.write_text("99999999 2026-01-01T00:00:00", encoding="utf-8")

        with mock.patch.object(q, "pid_alive", return_value=False):
            with qa_lote.LoteLock(q):
                self.assertTrue(lock.exists())
                self.assertIn(str(os.getpid()), lock.read_text())

        self.assertFalse(lock.exists())

    def test_lote_lock_de_proceso_vivo_no_se_roba(self):
        """Evita dos EJECUTAR simultaneos y duplicacion de PR."""
        lock = self.state / "lote.lock"
        lock.write_text("45678 2026-10-26T10:00:00", encoding="utf-8")

        with mock.patch.object(q, "pid_alive", return_value=True):
            with self.assertRaises(SystemExit):
                with qa_lote.LoteLock(q):
                    pass

        self.assertEqual(
            lock.read_text(encoding="utf-8"),
            "45678 2026-10-26T10:00:00",
        )

    def test_lote_git_fetch_fallido_permita_consultar_main(self):
        """Evita detener todo el lote por un fetch transitoriamente fallido."""
        lo = self.lote()
        llamadas = []

        def git(*args, check=True):
            llamadas.append(args)
            if args[0] == "fetch":
                raise RuntimeError("red no disponible")
            if args[:2] == ("rev-parse", "origin/main"):
                return "abc123456789"
            return ""

        with mock.patch.object(lo, "git", side_effect=git):
            sha = lo.main_sha()
            segunda = lo.main_sha()

        self.assertEqual(sha, "abc123456789")
        self.assertEqual(segunda, sha)
        self.assertEqual(
            sum(args[0] == "fetch" for args in llamadas),
            1,
        )

    def test_lote_ref_sin_ramas_no_fabrica_referencias(self):
        """Evita enviar ramas inexistentes cuando git devuelve salida vacia."""
        lo = self.lote()

        with mock.patch.object(lo, "git", return_value=""):
            refs = lo.refs()

        self.assertEqual(refs, {})

    def test_pr_comando_test_no_ejecuta_extensiones_desconocidas(self):
        """Evita ejecutar archivos no reconocidos como comandos arbitrarios."""
        self.assertEqual(
            qa_pr.Pr.comando_test("tests/comprobar.py"),
            ["python", "tests/comprobar.py"],
        )
        self.assertEqual(
            qa_pr.Pr.comando_test("qa/comprobar.mjs"),
            ["node", "qa/comprobar.mjs"],
        )
        self.assertIsNone(
            qa_pr.Pr.comando_test("qa/comprobar.bat")
        )
        self.assertIsNone(
            qa_pr.Pr.comando_test("qa/comprobar.exe")
        )

    def test_pr_interrupcion_no_se_confunde_con_fallo_de_test(self):
        """Evita marcar como test defectuoso una validacion interrumpida."""
        def runner(*args, **kwargs):
            return qa_lote.RC_ABORTADO, "parada solicitada"

        pr = qa_pr.Pr(
            q,
            gh=mock.Mock(),
            runner=runner,
            out=lambda *args: None,
        )

        with self.assertRaises(qa_pr.Interrumpido):
            pr.run(["python", "tests/prueba.py"], str(self.root))

    def test_consulta_jobs_miles_de_filas_en_tiempo_acotado(self):
        """Evita degradacion excesiva al seleccionar trabajos pendientes."""
        ahora = q.now()

        filas = [
            (
                f"config:volumen:{i}",
                "A",
                "zona:configuracion",
                "pendiente" if i % 7 == 0 else "hecho",
                "{}",
                0,
                ahora,
                ahora,
                ahora,
            )
            for i in range(5000)
        ]

        self.c.executemany(
            """
            INSERT INTO jobs(
                clave,tipo,area,estado,payload,intentos,
                no_antes,creado,actualizado
            ) VALUES(?,?,?,?,?,?,?,?,?)
            """,
            filas,
        )
        self.c.commit()

        inicio = time.monotonic()

        for _ in range(30):
            fila = q.next_job(self.c)
            self.assertIsNotNone(fila)
            self.assertEqual(fila["estado"], "pendiente")

        duracion = time.monotonic() - inicio

        self.assertLess(
            duracion,
            3.0,
            f"Seleccion de jobs demasiado lenta: {duracion:.3f}s",
        )


if __name__ == "__main__":
    unittest.main()
