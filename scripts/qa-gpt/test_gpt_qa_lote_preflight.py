import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones aisladas del preflight de lotes combinados y sus tests vecinos."""

import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import qa_lote_preflight as preflight


class FakePr:
    """Doble de PR sin acceso a GitHub, red ni repositorios reales."""

    def __init__(self, tests=None, results=None):
        self.tests = tests or {}
        self.results = results or {}
        self.executed = []
        self.git_calls = []
        self.cleaned = []
        self.q = SimpleNamespace(STATE=None)

    def _rutas_tests(self, db, ids):
        return sorted({
            path
            for proposal_id in ids
            for path in self.tests.get(proposal_id, [])
        })

    def comando_test(self, path):
        if path.startswith("tests/") and path.endswith(".py"):
            return ["python", path]
        return None

    def _test(self, worktree, path):
        self.executed.append((str(worktree), path))
        result = self.results.get(path, (0, "OK"))
        return result() if callable(result) else result

    def git(self, *args, cwd=None):
        self.git_calls.append((args, cwd))
        return 0, ""

    def limpiar(self, worktree, branch):
        self.cleaned.append((Path(worktree), branch))


class PreflightIsolation(unittest.TestCase):
    """Entorno temporal independiente para cada prueba."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.state.mkdir()

        self.pr = FakePr()
        self.pr.q.STATE = self.state

        self._patch_optional_globals()

    def _patch_optional_globals(self):
        """Aisla las rutas globales cuando los modulos del pipeline estan cargados."""
        try:
            import qa_gpt
        except ImportError:
            return

        replacements = {
            "STATE": self.state,
            "DB_PATH": self.state / "qa.sqlite3",
            "ROOT": self.root,
        }

        for name, value in replacements.items():
            if hasattr(qa_gpt, name):
                original = getattr(qa_gpt, name)
                setattr(qa_gpt, name, value)
                self.addCleanup(setattr, qa_gpt, name, original)

        lock = getattr(qa_gpt, "Lock", None)
        if lock is not None and hasattr(lock, "path"):
            original = lock.path
            lock.path = self.state / "qa.lock"
            self.addCleanup(setattr, lock, "path", original)

    def create_test(self, path, content="assert True\n"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def row(self, *ids):
        return {"propuestas": json.dumps(list(ids))}

    def validate(self, rows):
        return preflight.validar(self.pr, None, self.root, rows)

    def patch_changed(self, paths):
        p = patch.object(preflight, "cambiados", return_value=paths)
        mock = p.start()
        self.addCleanup(p.stop)
        return mock


class CombinedExecutionTests(PreflightIsolation):

    def test_shared_test_is_executed_once(self):
        """Evita ejecutar repetidamente el mismo test compartido por muchas propuestas."""
        self.create_test("tests/test_shared.py")
        self.pr.tests = {
            i: ["tests/test_shared.py"]
            for i in range(100)
        }

        ok, _, _ = self.validate([self.row(*range(100))])

        self.assertTrue(ok)
        self.assertEqual(len(self.pr.executed), 1)

    def test_execution_order_is_deterministic(self):
        """Evita resultados dependientes del orden de llegada de las propuestas."""
        paths = [
            "tests/test_z.py",
            "tests/test_a.py",
            "tests/test_m.py",
        ]
        for path in paths:
            self.create_test(path)

        self.pr.tests = {1: paths}

        ok, _, _ = self.validate([self.row(1)])

        self.assertTrue(ok)
        self.assertEqual(
            [path for _, path in self.pr.executed],
            sorted(paths),
        )

    def test_first_failure_stops_remaining_tests(self):
        """Evita consumir recursos ejecutando el resto del lote tras un fallo decisivo."""
        for name in ("a", "b", "c"):
            self.create_test(f"tests/test_{name}.py")

        self.pr.tests = {
            1: [
                "tests/test_a.py",
                "tests/test_b.py",
                "tests/test_c.py",
            ]
        }
        self.pr.results["tests/test_b.py"] = (1, "FAIL")

        ok, _, failed = self.validate([self.row(1)])

        self.assertFalse(ok)
        self.assertEqual(failed, "tests/test_b.py")
        self.assertEqual(len(self.pr.executed), 2)

    def test_missing_test_does_not_execute_other_tests(self):
        """Impide validar un lote incompleto cuando falta un test acumulado."""
        self.create_test("tests/test_z.py")
        self.pr.tests = {
            1: ["tests/test_a_missing.py", "tests/test_z.py"]
        }

        ok, detail, failed = self.validate([self.row(1)])

        self.assertFalse(ok)
        self.assertEqual(failed, "tests/test_a_missing.py")
        self.assertIn("ausente", detail)
        self.assertEqual(self.pr.executed, [])

    def test_unsupported_test_command_is_rejected(self):
        """Evita ejecutar comandos no autorizados procedentes de propuestas."""
        self.create_test("tests/test_custom.sh")
        self.pr.tests = {1: ["tests/test_custom.sh"]}

        ok, detail, failed = self.validate([self.row(1)])

        self.assertFalse(ok)
        self.assertEqual(failed, "tests/test_custom.sh")
        self.assertIn("no ejecutable", detail)
        self.assertFalse(self.pr.executed)

    def test_infrastructure_failure_preserves_retry_state(self):
        """Evita clasificar un entorno indisponible como defecto del parche."""
        self.create_test("tests/test_browser.py")
        self.pr.tests = {1: ["tests/test_browser.py"]}
        self.pr.results["tests/test_browser.py"] = (
            125, "browser unavailable"
        )

        ok, detail, failed = self.validate([self.row(1)])

        self.assertIsNone(ok)
        self.assertIsNone(failed)
        self.assertIn("entorno no disponible", detail)

    def test_infrastructure_failure_stops_later_tests(self):
        """Evita continuar validaciones cuando el entorno ya no permite ejecutarlas."""
        self.create_test("tests/test_a.py")
        self.create_test("tests/test_b.py")
        self.pr.tests = {
            1: ["tests/test_a.py", "tests/test_b.py"]
        }
        self.pr.results["tests/test_a.py"] = (125, "no environment")

        ok, _, _ = self.validate([self.row(1)])

        self.assertIsNone(ok)
        self.assertEqual(len(self.pr.executed), 1)

    def test_failure_output_is_bounded(self):
        """Evita almacenar salidas enormes de tests fallidos en el estado del lote."""
        self.create_test("tests/test_large.py")
        self.pr.tests = {1: ["tests/test_large.py"]}
        self.pr.results["tests/test_large.py"] = (
            1, "X" * 100_000 + "FINAL_ERROR"
        )

        ok, detail, _ = self.validate([self.row(1)])

        self.assertFalse(ok)
        self.assertLess(len(detail), 650)
        self.assertIn("FINAL_ERROR", detail)

    def test_empty_proposal_field_is_treated_as_empty_list(self):
        """Evita errores al recuperar filas con propuestas vacias de SQLite."""
        ok, detail, failed = self.validate([
            {"propuestas": None},
            {"propuestas": ""},
        ])

        self.assertFalse(ok)
        self.assertIsNone(failed)
        self.assertIn("sin tests", detail)

    # BUG: Un JSON corrupto en propuestas propaga JSONDecodeError y puede
    # interrumpir el ciclo completo; capturar el error y devolver fallo cerrado.
    def test_corrupt_proposals_fail_closed(self):
        """Evita que una fila SQLite corrupta derribe el proceso de preflight."""
        ok, detail, failed = self.validate([
            {"propuestas": "[1,"}
        ])

        self.assertFalse(ok)
        self.assertIsNone(failed)
        self.assertIn("propuestas", detail.lower())

    # BUG: json.loads acepta objetos y escalares, pero _rutas_tests espera
    # una lista de IDs; validar el tipo antes de consultar las propuestas.
    def test_non_list_proposals_fail_closed(self):
        """Evita que un esquema JSON incorrecto se interprete como IDs validos."""
        self.pr.tests = {"unexpected": ["tests/test_a.py"]}
        self.create_test("tests/test_a.py")

        ok, detail, _ = self.validate([
            {"propuestas": '{"unexpected": true}'}
        ])

        self.assertFalse(ok)
        self.assertIn("propuestas", detail.lower())


class OwnershipTests(PreflightIsolation):

    def test_shared_failure_has_all_owners(self):
        """Evita atribuir un test compartido a una sola correccion del lote."""
        self.pr.tests = {
            1: ["tests/test_shared.py"],
            2: ["tests/test_shared.py"],
            3: ["tests/test_other.py"],
        }

        owners = preflight.duenos(
            self.pr,
            None,
            [self.row(1), self.row(2), self.row(3)],
            "tests/test_shared.py",
        )

        self.assertEqual(owners, [0, 1])

    def test_unknown_failure_has_no_owner(self):
        """Evita culpar a una propuesta ajena por un test que no le pertenece."""
        self.pr.tests = {1: ["tests/test_a.py"]}

        owners = preflight.duenos(
            self.pr,
            None,
            [self.row(1)],
            "tests/test_unrelated.py",
        )

        self.assertEqual(owners, [])

    def test_duplicate_ids_do_not_duplicate_owners(self):
        """Evita repetir el indice de una fila con IDs duplicados."""
        self.pr.tests = {1: ["tests/test_a.py"]}

        owners = preflight.duenos(
            self.pr,
            None,
            [self.row(1, 1, 1)],
            "tests/test_a.py",
        )

        self.assertEqual(owners, [0])


class NeighborDiscoveryTests(PreflightIsolation):

    def test_neighbor_limit_is_respected(self):
        """Evita ejecutar cientos de tests vecinos por una sola modificacion."""
        for i in range(100):
            self.create_test(
                f"tests/test_{i:03d}.py",
                "build-reading-catalogue",
            )

        found = preflight.vecinos(
            self.root,
            ["scripts/build-reading-catalogue.py"],
            set(),
            maxi=12,
        )

        self.assertEqual(len(found), 12)
        self.assertEqual(len(set(found)), 12)

    def test_unreadable_neighbor_is_skipped(self):
        """Evita que un error de lectura impida analizar los demas tests."""
        self.create_test(
            "tests/test_good.py",
            "build-reading-catalogue",
        )
        self.create_test(
            "tests/test_bad.py",
            "build-reading-catalogue",
        )

        original = Path.read_text

        def controlled_read(path, *args, **kwargs):
            if path.name == "test_bad.py":
                raise OSError("access denied")
            return original(path, *args, **kwargs)

        with patch.object(Path, "read_text", controlled_read):
            found = preflight.vecinos(
                self.root,
                ["scripts/build-reading-catalogue.py"],
                set(),
            )

        self.assertEqual(found, ["tests/test_good.py"])

    def test_unrelated_changes_do_not_trigger_neighbor_scan(self):
        """Evita explorar tests vecinos para cambios sin codigo ejecutable relevante."""
        with patch.object(Path, "glob", side_effect=AssertionError(
            "Unexpected scan"
        )):
            found = preflight.vecinos(
                self.root,
                ["README.md", "data/example.json"],
                set(),
            )

        self.assertEqual(found, [])

    def test_neighbor_detection_uses_actual_source_content(self):
        """Evita seleccionar tests por su nombre cuando no cubren el fichero tocado."""
        self.create_test(
            "tests/test_catalogue.py",
            "assert True\n",
        )
        self.create_test(
            "tests/test_actual.py",
            "from scripts import build_reading_catalogue\n",
        )

        found = preflight.vecinos(
            self.root,
            ["scripts/build_reading_catalogue.py"],
            set(),
        )

        self.assertEqual(found, ["tests/test_actual.py"])

    def test_neighbor_scan_is_bounded_for_large_suite(self):
        """Evita crecimiento descontrolado del resultado con miles de tests."""
        for i in range(1500):
            self.create_test(
                f"tests/test_{i:04d}.py",
                "build-reading-catalogue",
            )

        found = preflight.vecinos(
            self.root,
            ["scripts/build-reading-catalogue.py"],
            set(),
            maxi=25,
        )

        self.assertEqual(len(found), 25)
        self.assertEqual(found, sorted(found))

    # BUG: vecinos busca solo tests/test*.py; una regresion en qa/*.mjs
    # puede llegar a CI sin preflight. Ampliar el descubrimiento a los
    # tests vecinos ejecutables reconocidos por comando_test.
    def test_javascript_neighbor_regression_is_discovered(self):
        """Evita omitir regresiones de navegador que afectan al codigo modificado."""
        self.create_test(
            "qa/reading-catalogue-browser.mjs",
            "import '../assets/reading-catalogue.js';",
        )

        found = preflight.vecinos(
            self.root,
            ["assets/reading-catalogue.js"],
            set(),
        )

        self.assertIn(
            "qa/reading-catalogue-browser.mjs",
            found,
        )


class MainBaselineTests(PreflightIsolation):

    def test_main_worktree_is_removed_after_success(self):
        """Evita acumular worktrees temporales tras comprobar main."""
        self.pr.results["tests/test_neighbor.py"] = (0, "OK")

        passed = preflight.pasa_en_main(
            self.pr,
            "tests/test_neighbor.py",
        )

        self.assertTrue(passed)
        self.assertEqual(len(self.pr.cleaned), 1)
        self.assertEqual(
            self.pr.cleaned[0][0],
            self.state / "pr" / "preflight-main",
        )

    def test_main_worktree_is_removed_after_test_exception(self):
        """Evita dejar worktrees huerfanos si el test baseline lanza una excepcion."""
        self.pr._test = Mock(side_effect=OSError("disk error"))

        with self.assertRaises(OSError):
            preflight.pasa_en_main(
                self.pr,
                "tests/test_neighbor.py",
            )

        self.assertEqual(len(self.pr.cleaned), 1)

    def test_git_failure_does_not_run_baseline_test(self):
        """Evita ejecutar tests sobre un worktree que Git no pudo crear."""
        self.pr.git = Mock(return_value=(1, "worktree add failed"))
        self.pr._test = Mock()

        result = preflight.pasa_en_main(
            self.pr,
            "tests/test_neighbor.py",
        )

        self.assertTrue(result)
        self.pr._test.assert_not_called()
        self.assertEqual(len(self.pr.cleaned), 1)

    def test_existing_baseline_is_cleaned_before_recreation(self):
        """Evita reutilizar un worktree de main contaminado por un ciclo anterior."""
        old = self.state / "pr" / "preflight-main"
        old.mkdir(parents=True)

        preflight.pasa_en_main(
            self.pr,
            "tests/test_neighbor.py",
        )

        self.assertEqual(len(self.pr.cleaned), 2)
        self.assertEqual(self.pr.cleaned[0][0], old)
        self.assertEqual(self.pr.cleaned[1][0], old)

    # BUG: El baseline devuelve False para cualquier codigo distinto de
    # cero, incluido RC_INFRA=125; esto permite aprobar un lote con un
    # vecino rojo cuando main no pudo comprobarse. Tratar 125 como
    # baseline desconocido y bloquear o reintentar, nunca aprobar.
    def test_unavailable_main_baseline_does_not_approve_regression(self):
        """Evita aceptar una regresion cuando el baseline falla por infraestructura."""
        self.create_test("tests/test_accumulated.py")
        self.create_test(
            "tests/test_neighbor.py",
            "build-reading-catalogue",
        )

        self.pr.tests = {
            1: ["tests/test_accumulated.py"]
        }

        self.pr.results = {
            "tests/test_accumulated.py": (0, "OK"),
            "tests/test_neighbor.py": lambda: (
                (125, "main environment unavailable")
                if self.pr.executed
                and Path(self.pr.executed[-1][0]).name == "preflight-main"
                else (1, "regression")
            ),
        }

        self.patch_changed([
            "scripts/build-reading-catalogue.py"
        ])

        ok, detail, _ = self.validate([self.row(1)])

        self.assertNotEqual(
            ok,
            True,
            "Un baseline indisponible no demuestra que el vecino ya fallaba",
        )


class ChangedFilesTests(PreflightIsolation):

    def test_git_diff_failure_does_not_expose_partial_output(self):
        """Evita interpretar una salida parcial de Git como lista fiable de cambios."""
        self.pr.git = Mock(return_value=(
            128,
            "fatal: ambiguous argument origin/main",
        ))

        changed = preflight.cambiados(
            self.pr,
            self.root,
        )

        self.assertIsNone(changed)  # desconocido, no "sin cambios"

    def test_missing_git_method_does_not_crash(self):
        """Evita errores en entornos donde el adaptador Git no esta disponible."""
        pr = SimpleNamespace()

        changed = preflight.cambiados(
            pr,
            self.root,
        )

        self.assertEqual(changed, [])

    # BUG: cambiados devuelve [] si git diff falla y validar interpreta
    # esa lista como ausencia de vecinos. Devolver un estado de error
    # distinguible y bloquear el lote hasta recuperar origin/main.
    def test_git_diff_failure_does_not_silently_skip_neighbors(self):
        """Evita aprobar lotes sin verificar vecinos cuando falla Git."""
        self.create_test("tests/test_accumulated.py")
        self.create_test(
            "tests/test_neighbor.py",
            "build-reading-catalogue",
        )

        self.pr.tests = {
            1: ["tests/test_accumulated.py"]
        }
        self.pr.git = Mock(return_value=(
            128,
            "fatal: origin/main unavailable",
        ))

        ok, detail, _ = self.validate([self.row(1)])

        self.assertNotEqual(
            ok,
            True,
            "El fallo de Git no equivale a ausencia de cambios",
        )


if __name__ == "__main__":
    unittest.main()
