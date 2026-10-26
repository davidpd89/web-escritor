import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Integración offline de qa_gpt, qa_lote y qa_pr con Git temporal y SQLite.

Cubre:
- Preparación de propuestas y ramas.
- Agrupación por área y conservación de identificadores.
- Validación local y remota simulada.
- Reanudación e idempotencia.
- Protección de main.
- Selección de correcciones y comprobaciones de CI.
- Persistencia, unicidad y consultas con miles de filas.

Compatible con Python 3.11 y Windows.
No requiere acceso a GitHub ni a la red.
"""

import json
import os
import sqlite3
import subprocess
import tempfile
import time
import unittest
from collections import Counter
from unittest.mock import Mock, patch

import qa_gpt as q
import qa_lote as L
import qa_pr as P


OK_PY = (
    "import unittest\n"
    "class TestSmoke(unittest.TestCase):\n"
    "    def test_ok(self): self.assertTrue(True)\n"
)

FAIL_PY = (
    "import unittest\n"
    "class TestSmoke(unittest.TestCase):\n"
    "    def test_fallo(self): self.assertEqual(1, 2)\n"
)

WF = """name: QA temporal
on:
  workflow_dispatch:
  pull_request:
    paths:
      - 'tests/**'
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: python -m unittest discover -s tests
"""


def git(*args, cwd):
    result = subprocess.run(
        [
            "git",
            "-c", "user.name=QA Test",
            "-c", "user.email=qa@example.invalid",
            *args,
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    if result.returncode:
        raise AssertionError(
            f"git {args!r}: {result.returncode}\n{result.stderr}"
        )
    return result.stdout.strip()


class FakeGh:
    """Simula GitHub Actions sin ejecutar gh, red ni git push."""

    def __init__(self):
        self.remote = {}
        self.runs_ = []
        self.dispatches = []
        self.pushes = []
        self.next_id = 100
        self.caido = False
        self.scope = {"repo", "workflow"}
        self.resultado = "ok"

    def check(self):
        if self.caido:
            raise L.GhError("HTTP 502 simulado")

    def ok(self):
        self.check()
        return True

    def scopes(self):
        self.check()
        return self.scope

    def remotos(self):
        self.check()
        return dict(self.remote)

    def remote_sha(self, rama):
        self.check()
        return self.remote.get(rama)

    def push(self, sha, rama):
        self.check()
        self.remote[rama] = sha
        self.pushes.append((rama, sha))

    def runs(self, wf, rama):
        self.check()
        return [
            dict(r)
            for r in self.runs_
            if r["wf"] == wf and r["rama"] == rama
        ]

    def run(self, rid):
        self.check()
        return next(
            dict(r)
            for r in self.runs_
            if r["databaseId"] == rid
        )

    def workflow_ref(self):
        self.check()
        return "main"

    def dispatch(self, wf, rama, ref=None, campos=None):
        self.check()
        self.next_id += 1
        self.dispatches.append((wf, rama))

        title = (
            f"QA GPT {campos['modo']} {campos['sha']}"
            if campos else wf
        )

        self.runs_.append({
            "wf": wf,
            "rama": rama,
            "databaseId": self.next_id,
            "headSha": self.remote[rama],
            "status": "queued",
            "conclusion": None,
            "url": f"https://example.invalid/runs/{self.next_id}",
            "event": "workflow_dispatch",
            "displayTitle": title,
            "campos": campos,
        })

    def runs_grupo(self, sha):
        self.check()
        return [
            dict(r)
            for r in self.runs_
            if r["wf"] == L.GRUPO_WF
            and sha in (r.get("displayTitle") or "")
        ]

    def resultados(self, rid):
        self.check()

        r = next(
            r for r in self.runs_
            if r["databaseId"] == rid
        )

        campos = r.get("campos") or {}
        rutas = [
            x.split(":", 1)[-1]
            for x in campos.get("tests", "").split()
        ]

        clase = self.resultado

        return {
            "modo": campos.get("modo", "regresion"),
            "resumen": {clase: len(rutas)},
            "tests": [
                {
                    "ruta": ruta,
                    "exe": "python",
                    "rc": 0 if clase == "ok" else 1,
                    "clase": clase,
                    "salida": (
                        "AssertionError: defecto"
                        if clase == "hallazgo" else ""
                    ),
                }
                for ruta in rutas
            ],
        }

    def log_failed(self, rid):
        self.check()
        return "AssertionError: fallo simulado"

    def tick(self, conclusion="success"):
        for r in self.runs_:
            if r["status"] == "queued":
                r["status"] = "in_progress"
            elif r["status"] == "in_progress":
                r["status"] = "completed"
                r["conclusion"] = conclusion


class BaseE2E(unittest.TestCase):
    """Aísla todos los recursos persistentes del pipeline."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            ignore_cleanup_errors=True
        )
        self.addCleanup(self.tmp.cleanup)

        self.base = Path(self.tmp.name)
        self.src = self.base / "src"
        self.bare = self.base / "origin.git"
        self.state = self.base / "state"

        originals = {
            "STATE": q.STATE,
            "DB_PATH": q.DB_PATH,
            "ROOT": q.ROOT,
            "WT": q.WT,
        }
        original_lock = q.Lock.path

        def restore():
            for name, value in originals.items():
                setattr(q, name, value)
            q.Lock.path = original_lock

        self.addCleanup(restore)

        q.STATE = self.state
        q.DB_PATH = self.state / "estado.db"
        q.ROOT = self.src
        q.WT = self.state / "wt"
        q.Lock.path = self.state / "worker.lock"

        # Windows: las llamadas internas a subprocess.run(text=True)
        # que omiten encoding pueden usar cp1252. Git produce ocasionalmente
        # bytes que no son decodificables con esa página de códigos.
        #
        # Se normaliza únicamente el entorno de pruebas. No se atribuye
        # a un fallo funcional del pipeline un error de decodificación
        # producido por la configuración regional del proceso.
        original_run = subprocess.run

        def run_utf8(*args, **kwargs):
            if kwargs.get("text") or kwargs.get("universal_newlines"):
                kwargs.setdefault("encoding", "utf-8")
                kwargs.setdefault("errors", "replace")
            return original_run(*args, **kwargs)

        runner_patch = patch.object(
            L.cob,
            "run",
            side_effect=run_utf8,
        )
        runner_patch.start()
        self.addCleanup(runner_patch.stop)

        subprocess.run(
            [
                "git", "init", "-q", "--bare", "-b", "main",
                str(self.bare),
            ],
            check=True,
            timeout=15,
        )
        subprocess.run(
            [
                "git", "init", "-q", "-b", "main",
                str(self.src),
            ],
            check=True,
            timeout=15,
        )

        workflow = self.src / ".github" / "workflows"
        workflow.mkdir(parents=True)
        (workflow / "tool-tests.yml").write_text(
            WF, encoding="utf-8"
        )

        tests = self.src / "tests"
        tests.mkdir()
        (tests / "test-base.py").write_text(
            OK_PY, encoding="utf-8"
        )

        git("add", "-A", cwd=self.src)
        git("commit", "-qm", "base", cwd=self.src)
        git(
            "remote", "add", "origin", str(self.bare),
            cwd=self.src,
        )
        git("push", "-q", "origin", "main", cwd=self.src)
        git("fetch", "-q", "origin", cwd=self.src)

        self.main_original = git(
            "rev-parse", "main", cwd=self.src
        )

        self.c = q.db()
        self.addCleanup(self.c.close)

        self.gh = FakeGh()
        self.output = []
        self.sequence = 0

        self.cfg = {
            "poll_s": 0,
            "concurrencia": 2,
            "max_horas": 1,
            "tam_lote": 30,
            "node_modules": str(self.base / "no-node-modules"),
            "timeout_test_s": 15,
        }

    def nueva_propuesta(
        self,
        nombre,
        contenido=OK_PY,
        area="zona:e2e",
        categoria="regresion",
        estado="aceptada",
    ):
        self.sequence += 1
        pid = self.sequence
        ruta = f"tests/test-{nombre}.py"

        datos = {
            "via": "lote",
            "titulo": nombre,
            "categoria": categoria,
            "workflow": "tool-tests.yml",
            "ficheros_nuevos": [{
                "ruta": ruta,
                "contenido": contenido,
            }],
            # Contrato real de qa_lote.Lote.comandos():
            # utiliza los pasos explícitos o los comandos normalizados.
            # No debe inferirse que el nombre de un fichero implica
            # automáticamente su ejecución.
            "pasos": [{
                "argv": ["python", ruta],
                "env": {},
            }],
        }

        self.c.execute(
            """INSERT INTO propuestas
               (id, huella, area, titulo, datos,
                estado, creado, actualizado)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pid,
                f"huella-{pid}",
                area,
                nombre,
                json.dumps(datos),
                estado,
                q.now(),
                q.now(),
            ),
        )
        self.c.commit()
        return pid

    def preparar_rama(
        self,
        nombre,
        contenido=OK_PY,
        area=None,
        categoria="regresion",
    ):
        area = area or f"zona:{nombre}"
        pid = self.nueva_propuesta(
            nombre, contenido, area, categoria, "preparada"
        )
        rama = f"gpt-qa/{nombre}"

        git(
            "checkout", "-q", "-b", rama, "origin/main",
            cwd=self.src,
        )

        ruta = f"tests/test-{nombre}.py"
        (self.src / ruta).write_text(
            contenido, encoding="utf-8"
        )

        git("add", "-A", cwd=self.src)
        git(
            "commit", "-qm", f"test {nombre}",
            cwd=self.src,
        )

        sha = git("rev-parse", "HEAD", cwd=self.src)
        git("checkout", "-q", "main", cwd=self.src)

        self.c.execute(
            "UPDATE propuestas SET rama=? WHERE id=?",
            (rama, pid),
        )
        self.c.execute(
            """INSERT INTO ramas
               (rama, area, ruta, sha, estado)
               VALUES (?, ?, ?, ?, 'preparada')""",
            (rama, area, "", sha),
        )
        self.c.commit()
        return pid, rama, sha

    def lote(self, **config):
        return L.Lote(
            q,
            self.gh,
            sleep=lambda _: self.gh.tick(),
            out=self.output.append,
            cfg={**self.cfg, **config},
        )

    def propuesta(self, pid):
        return self.c.execute(
            "SELECT * FROM propuestas WHERE id=?",
            (pid,),
        ).fetchone()

    def items(self):
        return self.c.execute(
            "SELECT * FROM lote_items ORDER BY clave"
        ).fetchall()

    def estado_item(self, rama):
        row = self.c.execute(
            "SELECT estado FROM lote_items WHERE rama=?",
            (rama,),
        ).fetchone()
        return row[0] if row else None

    def assert_main_intacto(self):
        self.assertEqual(
            git("rev-parse", "main", cwd=self.src),
            self.main_original,
        )
        self.assertEqual(
            git("rev-parse", "origin/main", cwd=self.src),
            self.main_original,
        )

    def assert_sin_duplicados(self):
        items = self.items()
        claves = [r["clave"] for r in items]
        self.assertEqual(len(claves), len(set(claves)))

        ids = []
        for row in items:
            ids.extend(json.loads(row["propuestas"]))

        self.assertEqual(len(ids), len(set(ids)))
        return ids


class TestStageIntegracion(BaseE2E):

    def test_stage_agrupa_propuestas_de_la_misma_area(self):
        """Evita perder propuestas cuando varias comparten rama y commit."""
        ids = [
            self.nueva_propuesta(f"grupo{i}")
            for i in range(3)
        ]

        q.stage(self.c)

        rows = [self.propuesta(pid) for pid in ids]
        self.assertTrue(
            all(r["estado"] == "preparada" for r in rows)
        )
        self.assertEqual(len({r["rama"] for r in rows}), 1)

        rama = rows[0]["rama"]
        archivos = git(
            "ls-tree", "-r", "--name-only", rama,
            cwd=self.src,
        ).splitlines()

        for i in range(3):
            self.assertIn(f"tests/test-grupo{i}.py", archivos)

        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM ramas WHERE rama=?",
                (rama,),
            ).fetchone()[0],
            1,
        )
        self.assert_main_intacto()

    def test_stage_separa_areas_distintas(self):
        """Evita mezclar tests de zonas independientes en una rama."""
        a = self.nueva_propuesta(
            "area-a", area="zona:primera"
        )
        b = self.nueva_propuesta(
            "area-b", area="zona:segunda"
        )

        q.stage(self.c)

        self.assertEqual(self.propuesta(a)["estado"], "preparada")
        self.assertEqual(self.propuesta(b)["estado"], "preparada")
        self.assertNotEqual(
            self.propuesta(a)["rama"],
            self.propuesta(b)["rama"],
        )
        self.assert_main_intacto()

    def test_stage_invalida_una_propuesta_sin_perder_la_siguiente(self):
        """Evita que un test inválido descarte otro válido del área."""
        malo = self.nueva_propuesta(
            "malo", "def roto(:\n"
        )
        bueno = self.nueva_propuesta("bueno")

        q.stage(self.c)

        self.assertEqual(self.propuesta(malo)["estado"], "invalida")
        self.assertEqual(self.propuesta(bueno)["estado"], "preparada")

        rama = self.propuesta(bueno)["rama"]
        archivos = git(
            "ls-tree", "-r", "--name-only", rama,
            cwd=self.src,
        )

        self.assertIn("tests/test-bueno.py", archivos)
        self.assertNotIn("tests/test-malo.py", archivos)

    def test_stage_no_duplica_al_repetir(self):
        """Evita commits y propuestas duplicados tras repetir INICIAR."""
        pid = self.nueva_propuesta("repetible")

        q.stage(self.c)
        rama = self.propuesta(pid)["rama"]
        sha = git("rev-parse", rama, cwd=self.src)

        q.stage(self.c)

        self.assertEqual(
            git("rev-parse", rama, cwd=self.src), sha
        )
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM ramas WHERE rama=?",
                (rama,),
            ).fetchone()[0],
            1,
        )
        self.assertEqual(self.propuesta(pid)["estado"], "preparada")

    def test_stage_no_deja_worktrees_activos(self):
        """Evita la acumulación de worktrees que agotó el disco."""
        for i in range(4):
            self.nueva_propuesta(
                f"limpieza{i}", area=f"zona:limpieza{i}"
            )

        q.stage(self.c)

        activos = git(
            "worktree", "list", "--porcelain",
            cwd=self.src,
        )
        self.assertEqual(activos.count("worktree "), 1)

        if q.WT.exists():
            self.assertEqual(list(q.WT.iterdir()), [])


class TestLoteIntegracion(BaseE2E):

    def test_stage_lote_actions_conserva_todas_las_propuestas(self):
        """Evita perder IDs al pasar de propuestas a validación remota."""
        ids = [
            self.nueva_propuesta(f"completa{i}")
            for i in range(4)
        ]
        q.stage(self.c)

        self.lote().ejecutar()

        capturados = self.assert_sin_duplicados()
        self.assertCountEqual(capturados, ids)

        self.assertEqual(len(self.items()), 1)
        self.assertEqual(self.items()[0]["estado"], "actions_ok")

        for pid in ids:
            self.assertEqual(
                self.propuesta(pid)["estado"], "ejecutada"
            )

        self.assert_main_intacto()

    def test_varias_ramas_mantienen_ids_independientes(self):
        """Evita que un lote asigne propuestas a la rama equivocada."""
        esperados = {}
        for i in range(3):
            pid, rama, sha = self.preparar_rama(f"rama{i}")
            esperados[rama] = pid

        self.lote().ejecutar()

        self.assertEqual(len(self.items()), 3)
        self.assertCountEqual(
            self.assert_sin_duplicados(),
            esperados.values(),
        )

        for row in self.items():
            self.assertEqual(
                json.loads(row["propuestas"]),
                [esperados[row["rama"]]],
            )
            self.assertEqual(row["estado"], "actions_ok")

    def test_doble_ejecucion_no_repite_dispatch(self):
        """Evita publicar dos veces el mismo test por doble clic."""
        for i in range(3):
            self.preparar_rama(f"doble{i}")

        self.lote().ejecutar()

        dispatches = list(self.gh.dispatches)
        pushes = list(self.gh.pushes)
        claves = [r["clave"] for r in self.items()]

        self.lote().ejecutar()

        self.assertEqual(self.gh.dispatches, dispatches)
        self.assertEqual(self.gh.pushes, pushes)
        self.assertEqual(
            [r["clave"] for r in self.items()], claves
        )
        self.assert_sin_duplicados()

    def test_caida_github_no_pierde_propuestas(self):
        """Evita cerrar como ejecutado un test sin evidencia remota."""
        pid, rama, _ = self.preparar_rama("caida")
        self.gh.caido = True

        self.lote().ejecutar()

        self.assertEqual(self.estado_item(rama), "local_ok")
        self.assertEqual(self.propuesta(pid)["estado"], "aprobada")
        self.assertEqual(len(self.gh.dispatches), 0)

        self.gh.caido = False
        self.lote().ejecutar()

        self.assertEqual(self.estado_item(rama), "actions_ok")
        self.assertEqual(self.propuesta(pid)["estado"], "ejecutada")
        self.assertEqual(len(self.gh.dispatches), 1)
        self.assert_sin_duplicados()

    def test_reinicio_desde_bd_persistida(self):
        """Evita perder el lote al cerrar EJECUTAR antes de validarlo."""
        pid, rama, sha = self.preparar_rama("reinicio")

        lo = self.lote()
        lid = lo.abrir_lote()
        lo.c.close()

        self.assertEqual(len(self.items()), 1)

        self.lote().ejecutar()

        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM lotes WHERE id=?",
                (lid,),
            ).fetchone()[0],
            1,
        )
        self.assertEqual(self.estado_item(rama), "actions_ok")
        self.assertEqual(self.propuesta(pid)["estado"], "ejecutada")
        self.assert_sin_duplicados()

    def test_nuevas_propuestas_durante_lote_abierto(self):
        """Evita el bucle de lotes cuando INICIAR prepara otra rama."""
        pid1, rama1, _ = self.preparar_rama("primera")

        lo = self.lote()
        lid = lo.abrir_lote()
        lo.c.close()

        pid2, rama2, _ = self.preparar_rama("segunda")

        lo2 = self.lote()
        lid2 = lo2.abrir_lote()
        lo2.c.close()

        self.assertEqual(lid, lid2)
        self.assertCountEqual(
            self.assert_sin_duplicados(),
            [pid1, pid2],
        )
        self.assertEqual(len(self.items()), 2)

        self.lote().ejecutar()

        self.assertEqual(self.estado_item(rama1), "actions_ok")
        self.assertEqual(self.estado_item(rama2), "actions_ok")

    def test_lote_respeta_limite_sin_descartar_restantes(self):
        """Evita que el límite de lote haga desaparecer trabajo preparado."""
        ids = [
            self.preparar_rama(f"limite{i}")[0]
            for i in range(5)
        ]

        lo = self.lote(limite=2)
        lo.abrir_lote()

        self.assertEqual(len(self.items()), 2)
        self.assertEqual(len(self.assert_sin_duplicados()), 2)

        pendientes = self.c.execute(
            "SELECT COUNT(*) FROM propuestas WHERE estado='preparada'"
        ).fetchone()[0]

        self.assertEqual(pendientes, 3)
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM propuestas WHERE id IN "
                "(?,?,?,?,?)", ids
            ).fetchone()[0],
            5,
        )
        lo.c.close()

    def test_main_no_cambia_durante_validacion(self):
        """Evita fusionar accidentalmente tests exploratorios en main."""
        self.preparar_rama("main-protegido")

        self.lote().ejecutar()

        self.assert_main_intacto()
        self.assertEqual(
            git("branch", "--show-current", cwd=self.src),
            "main",
        )

    def test_lote_almacena_sha_exacto(self):
        """Evita validar una revisión distinta de la preparada."""
        pid, rama, sha = self.preparar_rama("sha-exacto")

        self.lote().ejecutar()

        row = self.items()[0]
        self.assertEqual(row["sha"], sha)
        self.assertEqual(
            row["clave"], f"{rama}@{sha[:12]}"
        )
        self.assertEqual(self.gh.remote[rama], sha)
        self.assertEqual(self.propuesta(pid)["estado"], "ejecutada")


    def test_lote_no_reutiliza_sha_antiguo(self):
        """Evita asociar resultados antiguos a una revisión nueva."""
        pid, rama, sha = self.preparar_rama("revision")

        lo = self.lote()
        lo.abrir_lote()
        lo.c.close()

        primera = self.items()[0]
        self.assertEqual(primera["sha"], sha)

        git("checkout", "-q", rama, cwd=self.src)
        (self.src / "tests" / "test-revision.py").write_text(
            OK_PY + "\n# segunda revisión\n",
            encoding="utf-8",
        )
        git("add", "-A", cwd=self.src)
        git("commit", "-qm", "segunda revision", cwd=self.src)
        sha2 = git("rev-parse", "HEAD", cwd=self.src)
        git("checkout", "-q", "main", cwd=self.src)

        self.assertNotEqual(sha, sha2)

        self.c.execute(
            "UPDATE ramas SET sha=? WHERE rama=?",
            (sha2, rama),
        )
        self.c.commit()

        lo2 = self.lote()
        lo2.abrir_lote()
        lo2.c.close()

        claves = {r["clave"] for r in self.items()}
        self.assertIn(f"{rama}@{sha[:12]}", claves)
        self.assertIn(f"{rama}@{sha2[:12]}", claves)

        # Dos versiones del mismo ID no son propuestas independientes.
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM propuestas WHERE id=?",
                (pid,),
            ).fetchone()[0],
            1,
        )


class TestIntegracionPR(BaseE2E):

    def test_pr_deduplica_tests_de_varias_propuestas(self):
        """Evita ejecutar dos veces el mismo test al agrupar correcciones."""
        pid1 = self.nueva_propuesta("pr-uno")
        pid2 = self.nueva_propuesta("pr-dos")

        ruta = "tests/test-compartido.py"

        for pid in (pid1, pid2):
            row = self.propuesta(pid)
            datos = json.loads(row["datos"])
            datos["ficheros_nuevos"] = [{
                "ruta": ruta,
                "contenido": OK_PY,
            }]
            self.c.execute(
                "UPDATE propuestas SET datos=? WHERE id=?",
                (json.dumps(datos), pid),
            )
        self.c.commit()

        runner = Mock(return_value=(0, ""))
        pr = P.Pr(q, self.gh, runner, out=self.output.append)

        self.assertEqual(
            pr._rutas_tests(self.c, [pid1, pid2]),
            [ruta],
        )
        runner.assert_not_called()

    def test_pr_solo_selecciona_correcciones_aprobadas(self):
        """Evita abrir PRs de defectos sin aprobación de Claude."""
        P.Ciclo(
            q, self.gh, Mock(return_value=(0, "")),
            out=self.output.append,
        )

        self.c.execute(
            """INSERT INTO triaje
               (id, decision, clase, parche, pr_estado)
               VALUES (1001, 'descartar', 'defecto_web', '{}', '')"""
        )
        self.c.execute(
            """INSERT INTO triaje
               (id, decision, clase, parche, pr_estado)
               VALUES (1002, 'corregir', 'defecto_web', '{}', '')"""
        )
        self.c.execute(
            """INSERT INTO triaje
               (id, decision, clase, parche, pr_estado)
               VALUES (1003, 'corregir', 'test_no_fiable', '{}', '')"""
        )
        self.c.commit()

        pr = P.Pr(
            q, self.gh, Mock(return_value=(0, "")),
            out=self.output.append,
        )
        ids = [r["id"] for r in pr.candidatas(self.c)]

        self.assertEqual(ids, [1002])

    def test_pr_ci_requerida_pendiente_no_se_fusiona(self):
        """Evita fusionar un PR mientras falta una comprobación obligatoria."""
        checks = [{
            "name": "tests",
            "status": "IN_PROGRESS",
            "conclusion": None,
        }]

        self.assertEqual(
            P.ci_estado(checks, {"tests"}), "pendiente"
        )

    def test_pr_ci_roja_impide_integracion(self):
        """Evita fusionar una corrección cuya CI terminó fallando."""
        checks = [{
            "name": "tests",
            "status": "COMPLETED",
            "conclusion": "FAILURE",
        }]

        self.assertEqual(
            P.ci_estado(checks, {"tests"}), "rojo"
        )

    def test_pr_ci_verde_con_checks_opcionales_pendientes(self):
        """Evita bloquear una fusión por comprobaciones no requeridas."""
        checks = [
            {
                "name": "tests",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            },
            {
                "name": "informativo",
                "status": "IN_PROGRESS",
                "conclusion": None,
            },
        ]

        self.assertEqual(
            P.ci_estado(checks, {"tests"}), "verde"
        )

    def test_pr_no_confunde_estado_vacio_con_verde(self):
        """Evita fusionar cuando GitHub todavía no devuelve checks."""
        self.assertEqual(
            P.ci_estado([], {"tests"}), "pendiente"
        )
        self.assertEqual(
            P.ci_estado(None, {"tests"}), "pendiente"
        )


class TestPersistenciaYEscala(BaseE2E):

    def test_bd_reabierta_conserva_estados_finales(self):
        """Evita depender de estados que solo existían en memoria."""
        ids = [
            self.preparar_rama(f"persistencia{i}")[0]
            for i in range(3)
        ]

        self.lote().ejecutar()

        with sqlite3.connect(q.DB_PATH) as db2:
            estados = dict(
                db2.execute(
                    "SELECT id, estado FROM propuestas"
                ).fetchall()
            )
            claves = [
                r[0] for r in db2.execute(
                    "SELECT clave FROM lote_items"
                ).fetchall()
            ]

        self.assertTrue(
            all(estados[pid] == "ejecutada" for pid in ids)
        )
        self.assertEqual(len(claves), len(set(claves)))
        self.assertEqual(len(claves), 3)

    def test_reapertura_bd_no_duplica_tablas_ni_items(self):
        """Evita duplicaciones al ejecutar migraciones en cada arranque."""
        self.preparar_rama("migracion-e2e")
        self.lote().ejecutar()

        anteriores = [
            (r["clave"], r["estado"]) for r in self.items()
        ]

        for _ in range(3):
            c2 = q.db()
            c2.close()

        posteriores = [
            (r["clave"], r["estado"]) for r in self.items()
        ]

        self.assertEqual(anteriores, posteriores)
        self.assert_sin_duplicados()

    def test_miles_de_propuestas_no_duplican_huellas(self):
        """Evita aceptar dos propuestas con la misma huella persistente."""
        filas = [
            (
                f"perf-{i}", "zona:perf", f"test-{i}",
                "{}", "descartada", q.now(), q.now(),
            )
            for i in range(1500)
        ]

        self.c.executemany(
            """INSERT INTO propuestas
               (huella, area, titulo, datos, estado,
                creado, actualizado)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            filas,
        )
        self.c.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute(
                """INSERT INTO propuestas
                   (huella, area, titulo, datos, estado)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    "perf-500", "zona:perf", "duplicado",
                    "{}", "descartada",
                ),
            )

        self.c.rollback()

        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM propuestas "
                "WHERE huella LIKE 'perf-%'"
            ).fetchone()[0],
            1500,
        )

    def test_consulta_de_items_escala_con_miles_de_filas(self):
        """Evita una degradación desproporcionada al consultar el lote."""
        now = q.now()

        self.c.execute(
            """INSERT INTO lotes(inicio, estado)
               VALUES (?, 'en_curso')""",
            (now,),
        )
        lid = self.c.execute(
            "SELECT MAX(id) FROM lotes"
        ).fetchone()[0]

        filas = [
            (
                f"gpt-qa/perf{i}@{'a' * 12}",
                lid,
                f"gpt-qa/perf{i}",
                "a" * 40,
                "zona:perf",
                "[]",
                "actions_ok",
                "{}",
                now,
                now,
            )
            for i in range(2000)
        ]

        self.c.executemany(
            """INSERT INTO lote_items
               (clave, lote_id, rama, sha, area, propuestas,
                estado, runs, creado, actualizado)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            filas,
        )
        self.c.commit()

        inicio = time.monotonic()

        for _ in range(5):
            resultado = self.c.execute(
                """SELECT clave, estado FROM lote_items
                   WHERE lote_id=?
                   ORDER BY rama""",
                (lid,),
            ).fetchall()
            self.assertEqual(len(resultado), 2000)

        duracion = time.monotonic() - inicio

        self.assertLess(
            duracion, 5,
            f"Consulta de 2000 items demasiado lenta: {duracion:.2f}s",
        )

    def test_todas_las_propuestas_capturadas_tienen_referencia(self):
        """Evita propuestas aprobadas que desaparecen de lote_items."""
        ids = [
            self.preparar_rama(f"referencia{i}")[0]
            for i in range(5)
        ]

        lo = self.lote()
        lo.abrir_lote()
        lo.c.close()

        referencias = Counter(
            pid
            for item in self.items()
            for pid in json.loads(item["propuestas"])
        )

        self.assertEqual(set(referencias), set(ids))
        self.assertTrue(
            all(referencias[pid] == 1 for pid in ids)
        )

        for pid in ids:
            self.assertEqual(
                self.propuesta(pid)["estado"], "aprobada"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
