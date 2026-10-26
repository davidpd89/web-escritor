import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import sqlite3
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import qa_gpt
import qa_pr


class TestQaPr(unittest.TestCase):
    """Regresiones del flujo PR, aislamiento y seguridad de integración."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="qa_pr_test_")
        self.addCleanup(self.tmp.cleanup)

        self.base = Path(self.tmp.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        self.state = self.base / "estado"
        self.state.mkdir()
        self.db_path = self.state / "estado.db"

        self._replace(qa_gpt, "STATE", self.state)
        self._replace(qa_gpt, "DB_PATH", self.db_path)
        self._replace(qa_gpt, "ROOT", self.root)

        if hasattr(qa_gpt, "Lock"):
            self._replace(
                qa_gpt.Lock,
                "path",
                self.state / "trabajador.lock",
            )

        self.q = SimpleNamespace(
            ROOT=self.root,
            STATE=self.state,
            DB_PATH=self.db_path,
            CFG={"flujo": {"modo_pr": "lote"}},
            now=lambda: "2026-10-26T09:00:00",
        )

        self.gh = Mock()
        self.runner = Mock(return_value=(0, ""))
        self.pr = qa_pr.Pr(
            self.q, self.gh, self.runner, out=lambda *a: None
        )
        self.ciclo = qa_pr.Ciclo(
            self.q, self.gh, self.runner, out=lambda *a: None
        )

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.addCleanup(self.conn.close)

        self.conn.executescript("""
            CREATE TABLE triaje (
                id INTEGER PRIMARY KEY,
                firma TEXT,
                clase TEXT,
                decision TEXT,
                decision_json TEXT,
                parche TEXT,
                propuestas TEXT,
                items TEXT,
                analisis TEXT,
                validacion TEXT,
                evidencia TEXT,
                arreglo TEXT,
                causa_raiz TEXT,
                prioridad TEXT,
                pr_estado TEXT,
                pr_detalle TEXT,
                pr_url TEXT,
                pr_numero INTEGER DEFAULT 0,
                pr_nueva INTEGER DEFAULT 0,
                pr_head TEXT,
                dev_estado TEXT,
                integracion TEXT,
                revision TEXT,
                revision_hash TEXT,
                intentos_dev INTEGER DEFAULT 0,
                actualizado TEXT
            );

            CREATE TABLE propuestas (
                id INTEGER PRIMARY KEY,
                datos TEXT
            );

            CREATE TABLE lote_items (
                clave TEXT PRIMARY KEY,
                propuestas TEXT,
                estado TEXT,
                actualizado TEXT
            );

            CREATE TABLE claude_llamadas (
                clave TEXT PRIMARY KEY
            );

            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                tipo TEXT,
                clave TEXT,
                estado TEXT
            );
        """)
        self.conn.commit()

    def _replace(self, obj, name, value):
        old = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(setattr, obj, name, old)

    def fila(self, **changes):
        data = {
            "id": 1,
            "firma": "firma001",
            "clase": "defecto_web",
            "decision": "corregir",
            "decision_json": json.dumps({
                "decision": "corregir",
                "criterio_aceptacion": "El test debe pasar",
            }),
            "parche": json.dumps({
                "ficheros": [{
                    "ruta": "assets/app.js",
                    "reemplazos": [{
                        "buscar": "return false",
                        "por": "return true",
                    }],
                }],
            }),
            "propuestas": "[]",
            "items": "[]",
            "analisis": "{}",
            "validacion": "{}",
            "evidencia": "AssertionError",
            "arreglo": "",
            "causa_raiz": "Fallo reproducible",
            "prioridad": "1",
            "pr_estado": "",
            "pr_detalle": "",
            "pr_url": None,
            "pr_numero": 0,
            "pr_nueva": 0,
            "pr_head": None,
            "dev_estado": None,
            "integracion": None,
            "revision": None,
            "revision_hash": None,
            "intentos_dev": 0,
            "actualizado": "2026-10-26T08:00:00",
        }
        data.update(changes)

        columns = list(data)
        sql = (
            "INSERT INTO triaje ("
            + ",".join(columns)
            + ") VALUES ("
            + ",".join("?" for _ in columns)
            + ")"
        )
        self.conn.execute(sql, [data[k] for k in columns])
        self.conn.commit()
        return self.obtener(data["id"])

    def obtener(self, ident=1):
        return self.conn.execute(
            "SELECT * FROM triaje WHERE id=?", (ident,)
        ).fetchone()

    def test_solo_causas_aprobadas_entran_en_cola(self):
        """Evita desarrollar parches sin aprobación explícita de Claude."""
        self.fila()
        self.fila(
            id=2, firma="firma002",
            decision="revisar",
        )
        self.fila(
            id=3, firma="firma003",
            clase="test_no_fiable",
        )
        self.fila(
            id=4, firma="firma004",
            pr_estado="pr_abierta",
        )
        self.fila(
            id=5, firma="firma005",
            parche=None,
        )

        ids = [r["id"] for r in self.pr.candidatas(self.conn)]

        self.assertEqual(ids, [1])

    def test_miles_de_causas_no_reabren_pr_terminadas(self):
        """Evita reintentos masivos sobre causas ya descartadas o integradas."""
        self.conn.executemany(
            """
            INSERT INTO triaje
            (id, firma, clase, decision, parche, pr_estado)
            VALUES (?, ?, 'defecto_web', 'corregir', ?, ?)
            """,
            [
                (
                    i,
                    f"firma{i}",
                    json.dumps({"ficheros": []}),
                    "integrada" if i % 2 else "descartada",
                )
                for i in range(1, 3001)
            ],
        )
        self.conn.commit()

        inicio = time.monotonic()
        result = self.pr.candidatas(self.conn)
        elapsed = time.monotonic() - inicio

        self.assertEqual(result, [])
        self.assertLess(elapsed, 3)

    def test_firma_duplicada_reutiliza_pr_existente(self):
        """Evita abrir dos PR para la misma causa tras reanudar el servicio."""
        self.fila(
            id=1,
            pr_estado="pr_abierta",
            pr_url="https://github.com/example/repo/pull/42",
        )
        row = self.fila(id=2, firma="firma001")

        result = self.pr.preparar(self.conn, row)

        self.assertEqual(result, "duplicada")
        self.assertEqual(self.obtener(2)["pr_estado"], "duplicada")
        self.assertEqual(
            self.obtener(2)["pr_url"],
            "https://github.com/example/repo/pull/42",
        )
        self.runner.assert_not_called()
        self.gh.assert_not_called()

    def test_sin_aprobacion_no_hace_fetch(self):
        """Impide tocar Git cuando Claude no autorizó la corrección."""
        row = self.fila(decision="revisar")

        result = self.pr.preparar(self.conn, row)

        self.assertEqual(result, "sin_aprobacion")
        self.assertEqual(
            self.obtener()["pr_estado"], "sin_aprobacion"
        )
        self.runner.assert_not_called()
        self.gh.assert_not_called()

    def test_fetch_fallido_deja_reintento_persistente(self):
        """Evita perder una corrección cuando falla la red antes del worktree."""
        row = self.fila()
        self.runner.return_value = (128, "fatal: network unavailable")

        result = self.pr.preparar(self.conn, row)

        self.assertEqual(result, "reintentar")
        self.assertEqual(self.obtener()["pr_estado"], "reintentar")
        self.assertIn("fetch", self.obtener()["pr_detalle"])
        self.gh.assert_not_called()

    def test_worktree_fallido_no_abre_pr(self):
        """Evita publicar una PR si no pudo crearse el árbol aislado."""
        row = self.fila()

        def fake_git(*args, **kwargs):
            if args[:2] == ("worktree", "add"):
                return 128, "fatal: worktree locked"
            return 0, ""

        with patch.object(self.pr, "git", side_effect=fake_git):
            with patch.object(self.pr, "limpiar"):
                result = self.pr.preparar(self.conn, row)

        self.assertEqual(result, "reintentar")
        self.assertIn("worktree", self.obtener()["pr_detalle"])
        self.gh.assert_not_called()

    def test_parche_no_puede_escribir_en_rutas_sensibles(self):
        """Impide modificar workflows, credenciales y el propio supervisor."""
        rutas = [
            ".github/workflows/deploy.yml",
            "scripts/qa-gpt/qa_pr.py",
            "package-lock.json",
            ".env.production",
            "config/secret.json",
            "../fuera.py",
            r"C:\GIT\web-escritor\index.html",
        ]

        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertIsNotNone(qa_pr.ruta_segura(ruta))

    def test_parche_rechaza_reemplazo_ambiguo(self):
        """Evita sustituir código equivocado cuando el patrón aparece dos veces."""
        parche = {
            "ficheros": [{
                "ruta": "assets/app.js",
                "reemplazos": [{
                    "buscar": "return false",
                    "por": "return true",
                }],
            }]
        }

        ok, problemas, normalizado = qa_pr.validar_parche(
            parche,
            lambda ruta: "return false\nreturn false\n",
        )

        self.assertFalse(ok)
        self.assertIsNone(normalizado)
        self.assertTrue(
            any("2 veces" in p for p in problemas),
            problemas,
        )

    def test_parche_rechaza_secretos_y_ficheros_repetidos(self):
        """Evita publicar credenciales o modificar dos veces el mismo fichero."""
        secreto = {
            "ficheros": [{
                "ruta": "assets/app.js",
                "reemplazos": [{
                    "buscar": "OLD",
                    "por": "password='supersecret123456'",
                }],
            }]
        }

        duplicado = {
            "ficheros": [
                {
                    "ruta": "assets/app.js",
                    "reemplazos": [{
                        "buscar": "OLD",
                        "por": "NEW",
                    }],
                },
                {
                    "ruta": "assets/app.js",
                    "reemplazos": [{
                        "buscar": "OLD",
                        "por": "OTHER",
                    }],
                },
            ]
        }

        for parche in (secreto, duplicado):
            with self.subTest(parche=parche):
                ok, problemas, norm = qa_pr.validar_parche(
                    parche, lambda ruta: "OLD"
                )
                self.assertFalse(ok)
                self.assertTrue(problemas)
                self.assertIsNone(norm)

    def test_aplicar_parche_revalida_antes_de_escribir(self):
        """Evita sobrescribir cambios concurrentes realizados tras validar el parche."""
        target = self.root / "assets" / "app.js"
        target.parent.mkdir()
        target.write_text("VERSION NUEVA", encoding="utf-8")

        parche = {
            "ficheros": [{
                "ruta": "assets/app.js",
                "reemplazos": [{
                    "buscar": "VERSION ANTIGUA",
                    "por": "VERSION CORREGIDA",
                }],
            }]
        }

        with self.assertRaises(ValueError):
            qa_pr.aplicar_parche(self.root, parche)

        self.assertEqual(
            target.read_text(encoding="utf-8"),
            "VERSION NUEVA",
        )

    def test_ci_rojo_tiene_precedencia_sobre_checks_verdes(self):
        """Impide fusionar una PR cuando algún check requerido ha fallado."""
        roll = [
            {
                "name": "Required merge gate",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            },
            {
                "name": "public-artifact-contract",
                "status": "COMPLETED",
                "conclusion": "FAILURE",
            },
        ]

        self.assertEqual(
            qa_pr.ci_estado(roll, [
                "Required merge gate",
                "public-artifact-contract",
            ]),
            "rojo",
        )

    def test_ci_requerido_ausente_no_es_verde(self):
        """Evita dar CI verde a una PR con verificaciones obligatorias ausentes."""
        roll = [{
            "name": "Required merge gate",
            "status": "COMPLETED",
            "conclusion": "SUCCESS",
        }]

        self.assertEqual(
            qa_pr.ci_estado(
                roll,
                ["Required merge gate", "public-artifact-contract"],
            ),
            "pendiente",
        )

    def test_ci_no_requerido_pendiente_no_bloquea(self):
        """Evita congelar lotes por comprobaciones opcionales lentas."""
        roll = [
            {
                "name": "Required merge gate",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            },
            {
                "name": "optional-audit",
                "status": "IN_PROGRESS",
            },
        ]

        self.assertEqual(
            qa_pr.ci_estado(roll, ["Required merge gate"]),
            "verde",
        )

    def test_main_compartido_obliga_a_actualizar(self):
        """Evita fusionar contra main cuando cambió infraestructura compartida."""
        self.gh.main_desde.return_value = (
            2, ["scripts/build-site-shell.py"]
        )

        motivo = self.ciclo._main_arriesgado(
            {"files": [{"path": "assets/app.js"}]},
            "sha-revisado",
        )

        self.assertIsNotNone(motivo)
        self.assertIn("infraestructura", motivo)

    def test_main_sin_solapes_no_reinicia_ci_innecesariamente(self):
        """Evita repetir veinte minutos de CI por cambios independientes."""
        self.gh.main_desde.return_value = (
            1, ["articulos/otro-articulo.html"]
        )

        motivo = self.ciclo._main_arriesgado(
            {"files": [{"path": "assets/app.js"}]},
            "sha-revisado",
        )

        self.assertIsNone(motivo)

    def test_comparacion_main_no_disponible_falla_cerrado(self):
        """Impide fusionar sin conocer los cambios recientes de main."""
        self.gh.main_desde.side_effect = RuntimeError(
            "GitHub API unavailable"
        )

        motivo = self.ciclo._main_arriesgado(
            {"files": [{"path": "assets/app.js"}]},
            "sha-revisado",
        )

        self.assertIsNotNone(motivo)
        self.assertIn("comparacion", motivo)

    def test_relanzamiento_rojo_solo_una_vez_tras_reinicio(self):
        """Evita el bucle de relanzamientos de CI que bloqueó las PR #859 y #865."""
        self.gh.rerun_fallidos.return_value = None
        run = {
            "databaseId": 859,
            "attempt": 1,
            "status": "completed",
            "conclusion": "failure",
        }

        primero = self.ciclo._relanzar_rojo(
            "Post-deploy deep audit", run
        )

        segundo_ciclo = qa_pr.Ciclo(
            self.q, self.gh, self.runner, out=lambda *a: None
        )
        segundo = segundo_ciclo._relanzar_rojo(
            "Post-deploy deep audit", run
        )

        self.assertTrue(primero)
        self.assertFalse(segundo)
        self.gh.rerun_fallidos.assert_called_once_with(859)

    def test_main_rojo_confirmado_no_se_relanzara_infinitamente(self):
        """Evita reintentar indefinidamente una auditoría realmente defectuosa."""
        run = {
            "databaseId": 865,
            "attempt": 2,
            "status": "completed",
            "conclusion": "failure",
        }

        result = self.ciclo._relanzar_rojo(
            "Live production PWA QA", run
        )

        self.assertFalse(result)
        self.gh.rerun_fallidos.assert_not_called()

    def test_regeneracion_sin_cambios_no_ejecuta_generadores(self):
        """Evita regeneraciones costosas cuando el parche no toca artefactos."""
        run = Mock(return_value=(0, ""))

        result = qa_pr.regenerar(
            run,
            self.root,
            ["tests/test_regresion.py"],
        )

        self.assertEqual(result, [])
        run.assert_not_called()

    def test_generador_sin_check_no_se_ejecuta_a_ciegas(self):
        """Evita regenerar artefactos con scripts que no admiten --check."""
        scripts = self.root / "scripts"
        scripts.mkdir()
        (scripts / "build-site-shell.py").write_text(
            "# generador simulado\n", encoding="utf-8"
        )

        run = Mock(return_value=(
            2, "error: unrecognized arguments: --check"
        ))

        result = qa_pr.regenerar(
            run, self.root, ["index.html"]
        )

        self.assertEqual(result, [])
        self.assertFalse(
            any(
                call.args[0] == [
                    "python", "scripts/build-site-shell.py"
                ]
                for call in run.call_args_list
            )
        )

    def test_regeneracion_cascada_tiene_limite(self):
        """Evita bucles infinitos de versiones de assets encadenados."""
        scripts = self.root / "scripts"
        scripts.mkdir()
        (scripts / "check-asset-versions.py").write_text(
            '    "app.js": "v1",\n',
            encoding="utf-8",
        )
        (scripts / "bump-asset-version.py").write_text(
            "# simulacion\n", encoding="utf-8"
        )

        assets = self.root / "assets"
        assets.mkdir()
        (assets / "app.js").write_text(
            "console.log('test');\n", encoding="utf-8"
        )

        def run(cmd, cwd, timeout=300, **kwargs):
            if cmd[:3] == [
                "git", "diff", "--name-only"
            ]:
                return 0, "assets/app.js\n"
            if cmd[:3] == [
                "git", "diff", "HEAD"
            ]:
                return 0, ""
            return 0, ""

        result = qa_pr.regenerar(
            run, self.root, ["assets/app.js"]
        )

        self.assertLessEqual(
            sum(x.startswith("?v=") for x in result),
            1,
        )

    def test_revision_de_lote_usa_todas_las_causas(self):
        """Evita que Claude apruebe un lote revisando solo su primera corrección."""
        self.fila(
            id=1,
            pr_numero=77,
            pr_nueva=1,
            pr_estado="pr_abierta",
        )
        self.fila(
            id=2,
            firma="firma002",
            causa_raiz="Segunda corrección",
            pr_numero=77,
            pr_nueva=1,
            pr_estado="pr_abierta",
        )

        self.gh.pr_diff.return_value = (
            "diff --git a/assets/app.js b/assets/app.js\n"
            "+correccion\n"
        )

        revision = {
            "veredicto": "integrar",
            "riesgo": "bajo",
            "cumple_criterio": True,
            "motivos": [],
        }

        with patch.object(
            self.ciclo,
            "_revisar_grupo",
            return_value=revision,
        ) as revisar:
            result = self.ciclo.revisar(
                self.conn, self.obtener(1), "sha-final"
            )

        self.assertEqual(result, revision)
        grupo = revisar.call_args.args[1]
        self.assertEqual(
            {row["id"] for row in grupo},
            {1, 2},
        )

        for ident in (1, 2):
            self.assertEqual(
                self.obtener(ident)["revision_hash"],
                "sha-final",
            )

    def test_fallo_de_diff_no_marca_revision_completada(self):
        """Evita reutilizar una revisión inexistente tras un fallo de GitHub."""
        row = self.fila(
            pr_numero=78,
            pr_nueva=1,
            pr_estado="pr_abierta",
        )

        self.gh.pr_diff.side_effect = RuntimeError(
            "HTTP 502"
        )

        result = self.ciclo.revisar(
            self.conn, row, "sha-final"
        )

        self.assertIsNone(result)
        self.assertIsNone(self.obtener()["revision_hash"])

    def test_registro_de_fusion_es_persistente_y_utc(self):
        """Evita perder el freno postdespliegue al reiniciar EJECUTAR."""
        self.ciclo._anotar_fusion(873)

        marca = self.state / "lote" / "ultima_fusion.json"
        self.assertTrue(marca.exists())

        contenido = json.loads(
            marca.read_text(encoding="utf-8")
        )

        self.assertEqual(contenido["pr"], 873)
        self.assertTrue(contenido["utc"].endswith("Z"))

        nuevo = qa_pr.Ciclo(
            self.q, self.gh, self.runner, out=lambda *a: None
        )
        self.assertEqual(
            json.loads(
                (nuevo.q.STATE / "lote" / "ultima_fusion.json")
                .read_text(encoding="utf-8")
            )["pr"],
            873,
        )


if __name__ == "__main__":
    unittest.main()
