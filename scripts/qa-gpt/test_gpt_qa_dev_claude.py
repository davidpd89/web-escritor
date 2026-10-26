import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones aisladas de qa_dev_claude: elegibilidad, worktrees, Claude y parches."""

import json
import sqlite3
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import qa_gpt
import qa_pr
import qa_claude
import qa_dev_claude as dev


class TestQaDevClaude(unittest.TestCase):
    """Pruebas offline del desarrollo de correcciones mediante Claude."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="qa_dev_claude_")
        self.addCleanup(self.tmp.cleanup)

        self.base = Path(self.tmp.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        self.state = self.base / "estado"
        self.state.mkdir()
        self.db_path = self.state / "estado.db"

        self._replace(qa_gpt, "ROOT", self.root)
        self._replace(qa_gpt, "STATE", self.state)
        self._replace(qa_gpt, "DB_PATH", self.db_path)

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
            now=lambda: "2026-10-26T10:00:00",
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

            CREATE TABLE claude_llamadas (
                clave TEXT PRIMARY KEY
            );
        """)
        self.conn.commit()

        self.pr = Mock()
        self.pr.git.return_value = (0, "")
        self.pr.reproduce.return_value = True
        self.pr._rutas_tests.return_value = ["qa/test_defecto.py"]
        self.pr._traer_tests.return_value = None
        self.pr.limpiar.return_value = None

        self.pr.git.side_effect = self.git_simulado

        self.claude = Mock(
            return_value=(
                {"resultado": "corregido", "resumen": "Defecto corregido"},
                {},
            )
        )

    def _replace(self, obj, name, value):
        old = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(setattr, obj, name, old)

    def fila(self, **changes):
        data = {
            "id": 1,
            "firma": "defecto-001",
            "clase": "defecto_web",
            "decision": "corregir",
            "decision_json": json.dumps({
                "decision": "corregir",
                "criterio_aceptacion": "La función devuelve true",
                "archivos": ["assets/app.js"],
            }),
            "parche": None,
            "propuestas": "[]",
            "items": "[]",
            "analisis": "{}",
            "validacion": "{}",
            "evidencia": "AssertionError",
            "arreglo": "",
            "causa_raiz": "La función devuelve false",
            "prioridad": "1",
            "pr_estado": None,
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
            "actualizado": "2026-10-26T09:00:00",
        }
        data.update(changes)

        columns = list(data)
        self.conn.execute(
            "INSERT INTO triaje (" + ",".join(columns) + ") VALUES ("
            + ",".join("?" for _ in columns) + ")",
            [data[k] for k in columns],
        )
        self.conn.commit()
        return self.obtener(data["id"])

    def obtener(self, ident=1):
        return self.conn.execute(
            "SELECT * FROM triaje WHERE id=?",
            (ident,),
        ).fetchone()

    def git_simulado(self, *args, **kwargs):
        if args[:2] == ("worktree", "add"):
            wt = Path(args[4])
            wt.mkdir(parents=True, exist_ok=True)
            target = wt / "assets" / "app.js"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "function check() {\n  return true;\n}\n",
                encoding="utf-8",
            )
            return 0, ""

        if args[:2] == ("diff", "--name-only"):
            return 0, "assets/app.js\n"

        if args[:1] == ("show",):
            return 0, "function check() {\n  return false;\n}\n"

        return 0, ""

    def desarrollar(self, row=None):
        if row is None:
            row = self.obtener()

        with patch.object(dev.qa_claude, "llamar", self.claude):
            return dev.desarrollar(self.q, self.conn, self.pr, row)

    def test_elegible_prioriza_correcciones_sin_parche(self):
        """Evita gastar intentos GPT cuando Claude puede desarrollar directamente."""
        self.fila(
            id=1,
            parche='{"ficheros":[]}',
            pr_estado="validacion_fallida",
        )
        self.fila(id=2, parche=None)
        self.fila(id=3, parche=None, prioridad="2")

        rows = dev.elegible(self.conn, maxi=3)

        self.assertEqual([r["id"] for r in rows], [2, 3, 1])

    def test_elegible_excluye_decisiones_y_clases_no_aprobadas(self):
        """Impide desarrollar defectos que no tienen autorización de corrección."""
        self.fila(id=1, decision="revisar")
        self.fila(id=2, clase="test_no_fiable")
        self.fila(id=3, decision="descartar")
        self.fila(id=4, clase="defecto_web")

        rows = dev.elegible(self.conn, maxi=10)

        self.assertEqual([r["id"] for r in rows], [4])

    def test_elegible_admite_test_roto_aprobado(self):
        """Evita bloquear la reparación de tests rotos aprobados por triaje."""
        self.fila(clase="test_roto")

        rows = dev.elegible(self.conn)

        self.assertEqual([r["id"] for r in rows], [1])

    def test_elegible_no_repite_llamada_claude_registrada(self):
        """Evita pagar dos veces por una corrección ya enviada a Claude."""
        self.fila()
        self.conn.execute(
            "INSERT INTO claude_llamadas(clave) VALUES (?)",
            ("dev_claude2:1",),
        )
        self.conn.commit()

        self.assertEqual(dev.elegible(self.conn), [])

    def test_elegible_no_recupera_version_anterior_como_intento_nuevo(self):
        """Permite migrar intentos antiguos sin confundir las claves v1 y v2."""
        self.fila()
        self.conn.execute(
            "INSERT INTO claude_llamadas(clave) VALUES (?)",
            ("dev_claude:1",),
        )
        self.conn.commit()

        self.assertEqual(
            [r["id"] for r in dev.elegible(self.conn)],
            [1],
        )

    def test_elegible_descarta_ruta_prohibida_antes_de_claude(self):
        """Impide encargar correcciones que necesitan modificar infraestructura protegida."""
        self.fila(
            decision_json=json.dumps({
                "archivos": [
                    "assets/app.js",
                    "scripts/qa-gpt/qa_gpt.py",
                ]
            })
        )

        rows = dev.elegible(self.conn)

        self.assertEqual(rows, [])
        self.assertEqual(self.obtener()["dev_estado"], "ruta_prohibida")
        self.assertEqual(self.obtener()["pr_estado"], "descartada")
        self.assertIn("scripts/qa-gpt", self.obtener()["pr_detalle"])

    def test_elegible_miles_de_filas_respeta_maximo(self):
        """Evita que una cola grande dispare miles de desarrollos simultáneos."""
        self.conn.executemany(
            """
            INSERT INTO triaje
            (id, clase, decision, decision_json, prioridad)
            VALUES (?, 'defecto_web', 'corregir', '{}', '2')
            """,
            [(i,) for i in range(1, 3001)],
        )
        self.conn.commit()

        inicio = time.monotonic()
        rows = dev.elegible(self.conn, maxi=5)
        duracion = time.monotonic() - inicio

        self.assertEqual(len(rows), 5)
        self.assertEqual([r["id"] for r in rows], [1, 2, 3, 4, 5])
        self.assertLess(duracion, 3)

    def test_elegible_no_marca_como_disponible_un_desarrollo_activo(self):
        """Evita seleccionar dos veces una corrección que ya desarrolla Claude."""
        self.fila(dev_estado="en_desarrollo")

        self.assertEqual(dev.elegible(self.conn), [])

    def test_no_reproduce_evitar_llamada_claude(self):
        """Evita consumir Claude cuando el defecto ya no se reproduce en main."""
        self.fila()
        self.pr.reproduce.return_value = False

        result = self.desarrollar()

        self.assertEqual(result, "no_reproduce")
        self.pr._marca.assert_called_once()
        self.claude.assert_not_called()
        self.assertIsNone(self.obtener()["dev_estado"])
        self.pr.git.assert_not_called()

    def test_desarrollo_correcto_reencola_parche_validado(self):
        """Evita perder una corrección válida antes de que vuelva a validación."""
        self.fila()

        result = self.desarrollar()

        row = self.obtener()
        self.assertEqual(result, "reencolada")
        self.assertEqual(row["dev_estado"], "claude")
        self.assertIsNone(row["pr_estado"])

        parche = json.loads(row["parche"])
        self.assertEqual(parche["ficheros"][0]["ruta"], "assets/app.js")

        reemplazo = parche["ficheros"][0]["reemplazos"][0]
        self.assertIn("false", reemplazo["buscar"])
        self.assertIn("true", reemplazo["por"])

        self.pr.limpiar.assert_called_once()

    def test_desarrollo_utiliza_worktree_aislado_y_limites_claude(self):
        """Impide que Claude edite el checkout principal o ejecute sin límites."""
        self.fila()

        self.assertEqual(self.desarrollar(), "reencolada")

        kwargs = self.claude.call_args.kwargs

        self.assertEqual(
            kwargs["cwd"],
            self.state / "pr" / "qa-dev_1",
        )
        self.assertEqual(kwargs["timeout_s"], 1200)
        self.assertEqual(kwargs["max_usd"], 2.0)
        self.assertEqual(kwargs["max_turnos"], 30)
        self.assertFalse(kwargs["usar_cache"])
        self.assertIn("Edit", kwargs["herramientas"])

        self.assertNotEqual(kwargs["cwd"], self.root)

    def test_desarrollo_pasa_causa_y_criterio_a_claude(self):
        """Evita correcciones sin contexto que arreglan síntomas equivocados."""
        self.fila(
            causa_raiz="El filtro acepta registros duplicados",
            decision_json=json.dumps({
                "criterio_aceptacion": "Rechazar registros duplicados",
                "archivos": ["assets/app.js"],
            }),
        )

        self.desarrollar()

        args = self.claude.call_args.args
        entrada = args[5]

        self.assertIn("El filtro acepta registros duplicados", entrada)
        self.assertIn("Rechazar registros duplicados", entrada)
        self.assertIn("qa/test_defecto.py", entrada)

    def test_claude_no_puede_no_reencola_parche(self):
        """Evita convertir una respuesta negativa de Claude en corrección aprobada."""
        self.fila()
        self.claude.return_value = (
            {
                "resultado": "no_se_puede",
                "resumen": "Necesita modificar infraestructura",
            },
            {},
        )

        result = self.desarrollar()

        self.assertEqual(result, "no_se_puede")
        self.assertEqual(self.obtener()["dev_estado"], "claude_no_puede")
        self.assertIsNone(self.obtener()["parche"])
        self.pr.limpiar.assert_called_once()

    def test_error_claude_persistido_y_worktree_limpiado(self):
        """Evita dejar un worktree abandonado tras un error controlado de Claude."""
        self.fila()
        self.claude.side_effect = qa_claude.ClaudeError(
            "Claude CLI agotó el tiempo disponible"
        )

        result = self.desarrollar()

        self.assertEqual(result, "claude_fallo")
        self.assertEqual(self.obtener()["dev_estado"], "claude_fallo")
        self.assertIn("tiempo", self.obtener()["pr_detalle"])
        self.pr.limpiar.assert_called_once()

    def test_claude_modifica_ruta_prohibida_y_se_rechaza(self):
        """Impide que una edición inesperada de Claude altere ficheros protegidos."""
        self.fila()

        original = self.pr.git.side_effect

        def git(*args, **kwargs):
            if args[:2] == ("diff", "--name-only"):
                return 0, "scripts/qa-gpt/qa_gpt.py\n"
            return original(*args, **kwargs)

        self.pr.git.side_effect = git

        result = self.desarrollar()

        self.assertEqual(result, "invalido")
        self.assertEqual(self.obtener()["dev_estado"], "claude_invalido")
        self.assertIsNone(self.obtener()["parche"])
        self.pr.limpiar.assert_called_once()

    def test_claude_no_puede_anadir_ficheros_nuevos(self):
        """Evita aceptar archivos nuevos que el formato buscar/por no soporta."""
        self.fila()

        original = self.pr.git.side_effect

        def git(*args, **kwargs):
            if args[:1] == ("show",):
                return 128, "fatal: path does not exist"
            return original(*args, **kwargs)

        self.pr.git.side_effect = git

        result = self.desarrollar()

        self.assertEqual(result, "invalido")
        self.assertIn("fichero nuevo", self.obtener()["pr_detalle"])
        self.assertIsNone(self.obtener()["parche"])

    def test_claude_sin_cambios_no_aprueba_correccion(self):
        """Evita aprobar una respuesta 'corregido' sin cambios verificables."""
        self.fila()

        original = self.pr.git.side_effect

        def git(*args, **kwargs):
            if args[:2] == ("diff", "--name-only"):
                return 0, ""
            return original(*args, **kwargs)

        self.pr.git.side_effect = git

        result = self.desarrollar()

        self.assertEqual(result, "invalido")
        self.assertEqual(self.obtener()["dev_estado"], "claude_invalido")
        self.assertIsNone(self.obtener()["parche"])

    def test_worktree_fallido_no_invoca_claude(self):
        """Evita ejecutar Claude sobre un checkout que no pudo prepararse."""
        self.fila()

        original = self.pr.git.side_effect

        def git(*args, **kwargs):
            if args[:2] == ("worktree", "add"):
                return 128, "fatal: worktree locked"
            return original(*args, **kwargs)

        self.pr.git.side_effect = git

        result = self.desarrollar()

        self.assertEqual(result, "worktree_fallo")
        self.claude.assert_not_called()
        self.pr.limpiar.assert_called_once()



    # BUG: elegible aplica json.loads a decision_json sin gestionar
    # JSONDecodeError ni TypeError. Una fila corrupta detiene el barrido
    # completo y bloquea también las correcciones válidas posteriores.
    # Arreglo mínimo: capturar errores por fila, marcarla como inválida
    # y continuar con el resto de candidatos.
    def test_decision_json_corrupto_no_bloquea_cola(self):
        """Evita que una fila corrupta impida desarrollar las correcciones siguientes."""
        self.fila(id=1, decision_json="{json roto")
        self.fila(id=2)

        rows = dev.elegible(self.conn, maxi=1)

        self.assertEqual([r["id"] for r in rows], [2])



    def test_diff_insercion_inicio_no_produce_buscar_vacio(self):
        """Evita generar reemplazos sin ancla al insertar código al principio."""
        antes = {"assets/app.js": "const a = 1;\nconst b = 2;\n"}
        despues = {
            "assets/app.js":
                "const nuevo = true;\nconst a = 1;\nconst b = 2;\n"
        }

        parche = dev.diff_a_parche(antes, despues)

        self.assertIsNotNone(parche)
        reemplazo = parche["ficheros"][0]["reemplazos"][0]
        self.assertTrue(reemplazo["buscar"].strip())
        self.assertIn("const nuevo", reemplazo["por"])

    def test_diff_repeticiones_amplia_contexto_unico(self):
        """Evita que el parche modifique la ocurrencia equivocada de código repetido."""
        antes = {
            "assets/app.js":
                "function a() {\nreturn false;\n}\n"
                "function b() {\nreturn false;\n}\n"
        }
        despues = {
            "assets/app.js":
                "function a() {\nreturn false;\n}\n"
                "function b() {\nreturn true;\n}\n"
        }

        parche = dev.diff_a_parche(antes, despues)

        self.assertIsNotNone(parche)
        reemplazo = parche["ficheros"][0]["reemplazos"][0]

        self.assertEqual(
            antes["assets/app.js"].count(reemplazo["buscar"]),
            1,
        )
        self.assertIn("true", reemplazo["por"])

    def test_diff_multifichero_conserva_alcance(self):
        """Evita perder cambios de una corrección que afecta a varios archivos."""
        antes = {
            "assets/a.js": "const a = false;\n",
            "assets/b.css": ".item { display: none; }\n",
        }
        despues = {
            "assets/a.js": "const a = true;\n",
            "assets/b.css": ".item { display: block; }\n",
        }

        parche = dev.diff_a_parche(antes, despues)

        self.assertEqual(
            {f["ruta"] for f in parche["ficheros"]},
            {"assets/a.js", "assets/b.css"},
        )

        ok, problemas, normalizado = qa_pr.validar_parche(
            parche,
            lambda ruta: antes[ruta],
        )

        self.assertTrue(ok, problemas)
        self.assertIsNotNone(normalizado)

    def test_diff_sin_cambios_no_genera_parche(self):
        """Evita reencolar una corrección cuando el contenido no ha cambiado."""
        texto = "function check() {\n  return true;\n}\n"

        self.assertIsNone(
            dev.diff_a_parche(
                {"assets/app.js": texto},
                {"assets/app.js": texto},
            )
        )


if __name__ == "__main__":
    unittest.main()
