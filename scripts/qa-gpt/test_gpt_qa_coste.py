import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones offline de qa_coste: consumo Actions, historial, BD y estimaciones."""

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

import qa_coste as coste
import qa_gpt as q


WORKFLOW = """name: QA
on:
  pull_request:
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - run: python -m unittest
  browser:
    runs-on: ubuntu-latest
    steps:
      - run: npm test
"""

REPO = "usuario/repositorio"
WF = "qa.yml"


def instante(segundos):
    """Devuelve un timestamp UTC reproducible."""
    base = datetime(2026, 10, 20, tzinfo=timezone.utc)
    return (base + timedelta(seconds=segundos)).isoformat().replace("+00:00", "Z")


def run_historico(numero, creado=0, iniciado=10, terminado=130):
    return {
        "databaseId": numero,
        "createdAt": instante(creado),
        "startedAt": instante(iniciado),
        "updatedAt": instante(terminado),
    }


def jobs_historicos(*duraciones):
    """Genera jobs secuenciales con duración en segundos."""
    resultado = []
    inicio = 10
    for duracion in duraciones:
        resultado.append({
            "s": instante(inicio),
            "c": instante(inicio + duracion),
        })
        inicio += duracion + 5
    return resultado


class Base(unittest.TestCase):
    """Aísla estado, SQLite, rutas y comandos externos del repositorio real."""

    def setUp(self):
        originales = {
            "STATE": q.STATE,
            "DB_PATH": q.DB_PATH,
            "ROOT": q.ROOT,
            "WT": q.WT,
            "LOCK": q.Lock.path,
        }

        def restaurar():
            q.STATE = originales["STATE"]
            q.DB_PATH = originales["DB_PATH"]
            q.ROOT = originales["ROOT"]
            q.WT = originales["WT"]
            q.Lock.path = originales["LOCK"]

        self.addCleanup(restaurar)

        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)

        self.root = Path(self.tmp.name)
        q.STATE = self.root / "state"
        q.DB_PATH = q.STATE / "qa.db"
        q.ROOT = self.root / "repo"
        q.WT = q.STATE / "worktrees"
        q.Lock.path = q.STATE / "worker.lock"

        q.STATE.mkdir(parents=True)
        q.ROOT.mkdir(parents=True)

        self.c = sqlite3.connect(":memory:")
        self.c.row_factory = sqlite3.Row
        self.addCleanup(self.c.close)

        self.c.executescript("""
            CREATE TABLE ramas (
                rama TEXT PRIMARY KEY,
                area TEXT,
                ruta TEXT,
                sha TEXT,
                estado TEXT
            );

            CREATE TABLE propuestas (
                id INTEGER PRIMARY KEY,
                rama TEXT,
                estado TEXT,
                datos TEXT
            );
        """)

        self.git = Mock(return_value="")
        self.fake_q = SimpleNamespace(
            db=lambda: self.c,
            git=self.git,
            CFG={"repo": REPO},
        )

    def rama(self, nombre, estado="preparada", sha="abc123"):
        rama = f"gpt-qa/{nombre}"
        self.c.execute(
            "INSERT INTO ramas(rama,area,ruta,sha,estado) VALUES(?,?,?,?,?)",
            (rama, "zona:tests", "", sha, estado),
        )
        self.c.commit()
        return rama

    def propuesta(
        self,
        identificador,
        rama,
        estado="preparada",
        workflow=WF,
        ruta="tests/test_nuevo.py",
        datos=None,
    ):
        if datos is None:
            datos = {
                "workflow": workflow,
                "ficheros_nuevos": [
                    {"ruta": ruta, "contenido": "def test_ok(): pass\n"}
                ],
            }

        contenido = datos if isinstance(datos, str) else json.dumps(datos)

        self.c.execute(
            "INSERT INTO propuestas(id,rama,estado,datos) VALUES(?,?,?,?)",
            (identificador, rama, estado, contenido),
        )
        self.c.commit()

    def configurar_git(self, workflows=None):
        workflows = workflows or {
            WF: WORKFLOW,
        }

        def git(*args, **kwargs):
            if args[:2] == ("ls-tree", "--name-only"):
                return "\n".join(
                    f".github/workflows/{nombre}"
                    for nombre in workflows
                )

            if args and args[0] == "show":
                especificacion = args[1]
                nombre = Path(especificacion.split(":", 1)[-1]).name
                return workflows.get(nombre, "")

            raise AssertionError(f"Comando git inesperado: {args!r}")

        self.git.side_effect = git

    def estimar(self, hist=None, ramas=None):
        if hist is None:
            hist = Mock(return_value=None)
        return coste.estimar(self.fake_q, ramas=ramas, hist=hist)


class JobsTests(Base):

    def test_jobs_reales_sin_confundir_steps(self):
        """Evita facturar los steps como jobs independientes."""
        self.assertEqual(coste.jobs_de(WORKFLOW), ["unit", "browser"])

    def test_jobs_ignora_claves_fuera_del_bloque(self):
        """Evita contar bloques YAML posteriores como jobs."""
        texto = """jobs:
  unit:
    runs-on: ubuntu-latest
permissions:
  contents: read
  falso:
    valor: 1
"""
        self.assertEqual(coste.jobs_de(texto), ["unit"])

    def test_jobs_ausentes_devuelve_lista_vacia(self):
        """Evita inventar consumo cuando el workflow carece de jobs."""
        self.assertEqual(coste.jobs_de("name: QA\non: push\n"), [])

    def test_jobs_admite_nombres_con_guiones_y_numeros(self):
        """Evita perder jobs válidos con identificadores habituales."""
        texto = """jobs:
  python-311:
    runs-on: windows-latest
  node-22:
    runs-on: ubuntu-latest
"""
        self.assertEqual(
            coste.jobs_de(texto),
            ["python-311", "node-22"],
        )

    def test_jobs_no_confunde_comentarios_con_definiciones(self):
        """Evita contar jobs deshabilitados mediante comentarios."""
        texto = """jobs:
  activo:
    runs-on: ubuntu-latest
  # deshabilitado:
  segundo:
    runs-on: ubuntu-latest
"""
        self.assertEqual(
            coste.jobs_de(texto),
            ["activo", "segundo"],
        )


class TiempoTests(Base):

    def test_segundos_utc_y_offsets_equivalentes(self):
        """Evita errores de duración al mezclar offsets ISO válidos."""
        a = "2026-10-20T10:00:00Z"
        b = "2026-10-20T12:01:00+02:00"
        self.assertEqual(coste._seg(a, b), 60)

    def test_duracion_negativa_se_limita_a_cero(self):
        """Evita costes negativos por timestamps invertidos."""
        self.assertEqual(
            coste._seg(instante(120), instante(10)),
            0,
        )

    def test_timestamp_corrupto_no_interrumpe_estimacion(self):
        """Evita abortar el informe por fechas malformadas."""
        self.assertIsNone(coste._seg("fecha-invalida", instante(20)))
        self.assertIsNone(coste._seg(instante(20), ""))
        self.assertIsNone(coste._seg(None, instante(20)))

    def test_duracion_con_fracciones_conserva_precision(self):
        """Evita truncar segundos antes de redondear minutos facturables."""
        a = "2026-10-20T10:00:00.000Z"
        b = "2026-10-20T10:01:00.500Z"
        self.assertAlmostEqual(coste._seg(a, b), 60.5)


class GitHubTests(Base):

    def test_gh_usa_timeout_y_no_ejecuta_procesos_reales(self):
        """Evita llamadas externas sin límite temporal."""
        resultado = SimpleNamespace(
            returncode=0,
            stdout='[{"databaseId": 1}]',
            stderr="",
        )

        with patch.object(coste.cob, "run", return_value=resultado) as run:
            datos = coste._gh("run", "list")

        self.assertEqual(datos, [{"databaseId": 1}])
        args, kwargs = run.call_args

        self.assertEqual(args[0], ["gh", "run", "list"])
        self.assertEqual(kwargs["timeout"], 120)
        self.assertTrue(kwargs["capture_output"])
        self.assertTrue(kwargs["text"])

    def test_gh_error_no_expone_salida_ilimitada(self):
        """Evita volcar respuestas enormes de GitHub en los informes."""
        resultado = SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="E" * 10000,
        )

        with patch.object(coste.cob, "run", return_value=resultado):
            with self.assertRaises(RuntimeError) as contexto:
                coste._gh("api", "repos/test/actions")

        self.assertLessEqual(len(str(contexto.exception)), 200)

    def test_gh_json_invalido_no_se_interpreta_como_exito(self):
        """Evita aceptar como historial una respuesta JSON corrupta."""
        resultado = SimpleNamespace(
            returncode=0,
            stdout="{json roto",
            stderr="",
        )

        with patch.object(coste.cob, "run", return_value=resultado):
            with self.assertRaises(json.JSONDecodeError):
                coste._gh("run", "list")

    def test_historial_sin_runs_no_consulta_jobs(self):
        """Evita llamadas innecesarias a la API cuando no hay ejecuciones."""
        with patch.object(coste, "_gh", return_value=[]) as gh:
            self.assertIsNone(coste.historial(REPO, WF))

        self.assertEqual(gh.call_count, 1)

    def test_historial_redondea_cada_job_independientemente(self):
        """Evita infravalorar minutos facturables sumando antes de redondear."""
        runs = [run_historico(101)]

        def gh(*args):
            if args[:2] == ("run", "list"):
                return runs
            return jobs_historicos(61, 1, 60)

        with patch.object(coste, "_gh", side_effect=gh):
            resultado = coste.historial(REPO, WF)

        self.assertEqual(resultado["facturable_min"], 4)
        self.assertEqual(resultado["n"], 1)

    def test_historial_usa_mediana_y_no_media(self):
        """Evita que una ejecución excepcional distorsione el presupuesto."""
        runs = [
            run_historico(1),
            run_historico(2),
            run_historico(3),
        ]
        duraciones = {1: 60, 2: 120, 3: 3600}

        def gh(*args):
            if args[:2] == ("run", "list"):
                return runs

            # API real:
            # repos/{repo}/actions/runs/{databaseId}/jobs
            # El identificador está inmediatamente después de "runs".
            partes = args[1].split("/")
            identificador = int(partes[partes.index("runs") + 1])
            return jobs_historicos(duraciones[identificador])

        with patch.object(coste, "_gh", side_effect=gh):
            resultado = coste.historial(REPO, WF)

        self.assertEqual(resultado["reloj_s"], 120)
        self.assertEqual(resultado["facturable_min"], 2)

    def test_historial_fallo_api_jobs_usa_tiempos_run(self):
        """Evita perder toda la estimación cuando falla la API de jobs."""
        runs = [run_historico(101, 0, 10, 130)]

        def gh(*args):
            if args[:2] == ("run", "list"):
                return runs
            raise RuntimeError("GitHub 502")

        with patch.object(coste, "_gh", side_effect=gh):
            resultado = coste.historial(REPO, WF)

        self.assertEqual(resultado["reloj_s"], 120)
        self.assertIsNone(resultado["facturable_min"])
        self.assertEqual(resultado["cola_s"], 10)

    def test_historial_jobs_incompletos_no_se_facturan(self):
        """Evita contar jobs sin inicio o final confirmado."""
        runs = [run_historico(101)]

        def gh(*args):
            if args[:2] == ("run", "list"):
                return runs
            return [
                {"s": instante(10), "c": None},
                {"s": None, "c": instante(30)},
                {"s": instante(40), "c": instante(100)},
            ]

        with patch.object(coste, "_gh", side_effect=gh):
            resultado = coste.historial(REPO, WF)

        self.assertEqual(resultado["facturable_min"], 1)
        self.assertEqual(resultado["reloj_s"], 60)

    def test_historial_timestamp_job_corrupto_no_rompe_mediana(self):
        """Evita abortar el presupuesto por un timestamp corrupto de Actions."""
        runs = [run_historico(101)]

        def gh(*args):
            if args[:2] == ("run", "list"):
                return runs
            return [
                {"s": "fecha-rota", "c": instante(100)},
                {"s": instante(10), "c": instante(70)},
            ]

        with patch.object(coste, "_gh", side_effect=gh):
            resultado = coste.historial(REPO, WF)

        self.assertEqual(resultado["facturable_min"], 1)
        self.assertIsNotNone(resultado["reloj_s"])


class EstimacionTests(Base):

    def test_sin_ramas_pendientes_no_invoca_git_ni_github(self):
        """Evita consumo y operaciones externas en lotes vacíos."""
        hist = Mock()

        resultado = self.estimar(hist=hist)

        self.assertEqual(resultado, [])
        hist.assert_not_called()
        self.git.assert_not_called()

    def test_ramas_finalizadas_no_generan_estimaciones(self):
        """Evita presupuestar ramas ya ejecutadas o descartadas."""
        for nombre, estado in [
            ("uno", "ejecutada"),
            ("dos", "descartada"),
            ("tres", "fallida"),
        ]:
            rama = self.rama(nombre, estado=estado)
            self.propuesta(len(nombre) + len(estado), rama)

        self.assertEqual(self.estimar(), [])
        self.git.assert_not_called()

    def test_propuestas_no_pendientes_no_gastan_actions(self):
        """Evita estimar coste de propuestas ya cerradas."""
        rama = self.rama("cerrada")
        self.propuesta(1, rama, estado="ejecutada")
        self.propuesta(2, rama, estado="rechazada")

        self.assertEqual(self.estimar(), [])
        self.git.assert_not_called()

    def test_rama_con_varias_propuestas_se_cuenta_una_vez(self):
        """Evita duplicar ejecuciones al agrupar propuestas en una rama."""
        rama = self.rama("grupo")
        self.propuesta(1, rama, ruta="tests/test_uno.py")
        self.propuesta(2, rama, ruta="tests/test_dos.py")
        self.configurar_git()

        with patch.object(
            coste.L,
            "workflows_que_ejecutan",
            return_value=[WF],
        ):
            filas = self.estimar(hist=Mock(return_value=None))

        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["propuestas"], [1, 2])
        self.assertEqual(filas[0]["jobs"], 2)

    def test_historial_compartido_se_consulta_una_vez(self):
        """Evita repetir llamadas GitHub por cada rama del mismo workflow."""
        for numero in range(1, 31):
            rama = self.rama(f"rama-{numero:03d}")
            self.propuesta(numero, rama)

        self.configurar_git()
        hist = Mock(return_value={
            "n": 3,
            "reloj_s": 120,
            "cola_s": 10,
            "facturable_min": 4,
        })

        with patch.object(
            coste.L,
            "workflows_que_ejecutan",
            return_value=[WF],
        ):
            filas = self.estimar(hist=hist)

        self.assertEqual(len(filas), 30)
        hist.assert_called_once_with(REPO, WF)

    def test_filtro_ramas_no_consulta_historial_de_otras(self):
        """Evita consultar costes de ramas excluidas del lote."""
        primera = self.rama("primera")
        segunda = self.rama("segunda")
        self.propuesta(1, primera)
        self.propuesta(2, segunda)
        self.configurar_git()

        with patch.object(
            coste.L,
            "workflows_que_ejecutan",
            return_value=[WF],
        ):
            filas = self.estimar(ramas=[segunda])

        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["test"], "segunda")

    def test_error_historial_no_cancela_otras_ramas(self):
        """Evita bloquear el informe completo por una caída de GitHub."""
        primera = self.rama("primera")
        segunda = self.rama("segunda")
        self.propuesta(1, primera)
        self.propuesta(2, segunda)
        self.configurar_git()

        hist = Mock(side_effect=RuntimeError("HTTP 503"))

        with patch.object(
            coste.L,
            "workflows_que_ejecutan",
            return_value=[WF],
        ):
            filas = self.estimar(hist=hist)

        self.assertEqual(len(filas), 2)
        self.assertIn("503", filas[0]["hist"]["error"])
        self.assertIn("503", filas[1]["hist"]["error"])
        hist.assert_called_once()

    def test_workflow_modificado_se_marca_para_scope(self):
        """Evita presentar como ejecutable una rama que modifica workflows."""
        rama = self.rama("modifica")
        self.propuesta(
            1,
            rama,
            datos={
                "workflow": WF,
                "ficheros_nuevos": [
                    {"ruta": "tests/test_nuevo.py", "contenido": "pass"}
                ],
                "ficheros_modificados": [
                    {
                        "ruta": ".github/workflows/qa.yml",
                        "contenido": WORKFLOW,
                    }
                ],
            },
        )
        self.configurar_git()

        with patch.object(
            coste.L,
            "workflows_que_ejecutan",
            return_value=[WF],
        ):
            filas = self.estimar()

        self.assertTrue(filas[0]["toca_workflow"])

        informe = coste.tabla(filas, scopes={"repo"})
        self.assertIn("BLOQUEADO", informe)
        self.assertIn("workflow", informe)

    def test_miles_de_propuestas_no_provocan_consultas_cuadraticas(self):
        """Evita crecimiento cuadrático de consultas al aumentar el lote."""
        rama = self.rama("masiva")

        datos = json.dumps({
            "workflow": WF,
            "ficheros_nuevos": [
                {"ruta": "tests/test_masivo.py", "contenido": "pass"}
            ],
        })

        self.c.executemany(
            "INSERT INTO propuestas(id,rama,estado,datos) VALUES(?,?,?,?)",
            [
                (numero, rama, "preparada", datos)
                for numero in range(1, 2001)
            ],
        )
        self.c.commit()
        self.configurar_git()

        consultas = []

        def registrar(sql):
            if sql.lstrip().upper().startswith("SELECT"):
                consultas.append(sql)
            return None

        self.c.set_trace_callback(registrar)
        self.addCleanup(lambda: self.c.set_trace_callback(None))

        with patch.object(
            coste.L,
            "workflows_que_ejecutan",
            return_value=[WF],
        ):
            filas = self.estimar()

        self.assertEqual(len(filas), 1)
        self.assertEqual(len(filas[0]["propuestas"]), 2000)
        self.assertLessEqual(len(consultas), 10)


class TablaTests(Base):

    def test_tabla_vacia_no_inventa_costes(self):
        """Evita informar ejecuciones inexistentes en un lote vacío."""
        informe = coste.tabla([])

        self.assertIn("0 tests", informe)
        self.assertIn("0 workflow(s)", informe)
        self.assertIn("0 jobs", informe)

    def test_tabla_sin_historial_no_inventa_duraciones(self):
        """Evita presentar tiempos estimados sin ejecuciones previas."""
        filas = [{
            "test": "nuevo",
            "propuestas": [1],
            "workflow": WF,
            "jobs": 2,
            "toca_workflow": False,
            "hist": None,
        }]

        informe = coste.tabla(filas, scopes={"repo"})

        self.assertIn("sin historial", informe)
        self.assertIn("listo para Actions", informe)

    def test_tabla_sin_workflow_exige_revision_humana(self):
        """Evita clasificar como apto un test no conectado a Actions."""
        filas = [{
            "test": "local",
            "propuestas": [1],
            "workflow": None,
            "toca_workflow": False,
        }]

        informe = coste.tabla(filas)

        self.assertIn("SOLO LOCAL", informe)
        self.assertIn("revision humana", informe)
        self.assertIn("0 aptos para Actions", informe)

    # BUG: historial() puede devolver reloj_s=None cuando GitHub entrega
    # ejecuciones sin timestamps válidos. tabla() aplica // y % sobre None,
    # provocando TypeError e impidiendo consultar el presupuesto.
    # Arreglo mínimo: mostrar "sin dato" para cada métrica ausente y
    # realizar operaciones aritméticas solo sobre valores numéricos.
    def test_tabla_historial_parcial_no_provoca_typeerror(self):
        """Evita que un historial incompleto impida consultar el presupuesto."""
        filas = [{
            "test": "parcial",
            "propuestas": [1],
            "workflow": WF,
            "jobs": 1,
            "toca_workflow": False,
            "hist": {
                "n": 2,
                "reloj_s": None,
                "cola_s": None,
                "facturable_min": None,
            },
        }]

        informe = coste.tabla(filas)

        self.assertIn("parcial", informe)
        self.assertIn("sin dato", informe)

    def test_tabla_con_scope_workflow_no_bloquea(self):
        """Evita exigir permisos adicionales cuando ya están concedidos."""
        filas = [{
            "test": "autorizado",
            "propuestas": [1],
            "workflow": WF,
            "jobs": 2,
            "toca_workflow": True,
            "hist": {
                "n": 3,
                "reloj_s": 125,
                "cola_s": 12,
                "facturable_min": 4,
            },
        }]

        informe = coste.tabla(
            filas,
            scopes={"repo", "workflow"},
        )

        self.assertIn("listo para Actions", informe)
        self.assertNotIn("BLOQUEADO", informe)
        self.assertIn("2m05s", informe)
        self.assertIn("4 min", informe)

    def test_tabla_resumen_distingue_ramas_y_workflows(self):
        """Evita confundir tres ramas con tres workflows distintos."""
        filas = [
            {
                "test": f"rama-{numero}",
                "propuestas": [numero],
                "workflow": WF,
                "jobs": 2,
                "toca_workflow": False,
                "hist": None,
            }
            for numero in range(1, 4)
        ]

        informe = coste.tabla(filas)

        self.assertIn("3 tests", informe)
        self.assertIn("1 workflow(s) distintos", informe)
        self.assertIn("6 jobs en total", informe)


if __name__ == "__main__":
    unittest.main()
