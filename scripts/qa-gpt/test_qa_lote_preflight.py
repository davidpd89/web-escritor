import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_lote_preflight import validate_combined


class FakePr:
    def __init__(self, tests, failures=None):
        self.tests = tests
        self.failures = failures or {}
        self.called = []

    def _rutas_tests(self, _db, ids):
        return sorted(set(path for i in ids for path in self.tests.get(i, [])))

    def comando_test(self, path):
        return ["python", path] if path.endswith(".py") else None

    def _test(self, _wt, path):
        self.called.append(path)
        return self.failures.get(path, (0, "pass"))


class VecinosTests(unittest.TestCase):
    def test_vecino_que_cita_el_generador_tocado(self):
        from qa_lote_preflight import vecinos
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "tests").mkdir()
            (Path(d, "tests/test-build-pagefind-index.py")).write_text("run('scripts/build-pagefind-index.py')")
            (Path(d, "tests/test-otro.py")).write_text("nada que ver")
            (Path(d, "tests/test-propio.py")).write_text("build-pagefind-index")
            self.assertEqual(vecinos(d, ["scripts/build-pagefind-index.py", "tests/test-propio.py", "script.js"], {"tests/test-propio.py"}),
                             ["tests/test-build-pagefind-index.py"])
            self.assertEqual(vecinos(d, ["script.js", "tests/x.py"], set()), [])  # nombres genericos o solo tests: sin vecinos

    def test_vecino_roto_que_pasa_en_main_bloquea_y_el_que_ya_fallaba_no(self):
        import qa_lote_preflight as P
        with tempfile.TemporaryDirectory() as d:
            for name in ("tests/test_a.py", "tests/test-vecino-generador.py"):
                p = Path(d, name); p.parent.mkdir(parents=True, exist_ok=True); p.write_text("build-generador")
            fake = FakePr({1: ["tests/test_a.py"]}, {"tests/test-vecino-generador.py": (1, "FAIL no eligible pages")})
            orig = (P.cambiados, P.pasa_en_main); self.addCleanup(lambda: (setattr(P, "cambiados", orig[0]), setattr(P, "pasa_en_main", orig[1])))
            P.cambiados = lambda pr, wt: ["scripts/build-generador.py"]
            P.pasa_en_main = lambda pr, path: True
            ok, det = P.validate_combined(fake, None, d, [{"propuestas": json.dumps([1])}])
            self.assertFalse(ok); self.assertIn("test-vecino-generador", det)
            P.pasa_en_main = lambda pr, path: False  # ya fallaba en main: no es culpa del lote
            ok, det = P.validate_combined(fake, None, d, [{"propuestas": json.dumps([1])}])
            self.assertTrue(ok); self.assertIn("ya fallaban en main", det)


class CombinedPreflightTests(unittest.TestCase):
    def test_runs_all_tests_on_combined_tree(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("tests/test_a.py", "tests/test_b.py"):
                p = Path(d, name); p.parent.mkdir(parents=True, exist_ok=True); p.write_text("pass")
            fake = FakePr({1:["tests/test_a.py"],2:["tests/test_b.py"]})
            result = validate_combined(fake, None, d, [
                {"propuestas": json.dumps([1])}, {"propuestas": json.dumps([2])}
            ])
            self.assertTrue(result[0], result[1])
            self.assertEqual(fake.called, ["tests/test_a.py","tests/test_b.py"])

    def test_prevents_ci_for_a_combined_regression(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "tests/test_a.py"); p.parent.mkdir(parents=True); p.write_text("pass")
            fake = FakePr({1:["tests/test_a.py"]},{"tests/test_a.py":(1,"AssertionError: regression")})
            good, detail = validate_combined(fake, None, d, [{"propuestas":"[1]"}])
            self.assertFalse(good)
            self.assertIn("AssertionError",detail)

    def test_fails_closed_for_missing_test(self):
        with tempfile.TemporaryDirectory() as d:
            fake=FakePr({1:["tests/missing.py"]})
            good, _ = validate_combined(fake,None,d,[{"propuestas":"[1]"}])
            self.assertFalse(good)

    def test_fails_closed_for_no_tests(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(validate_combined(FakePr({}),None,d,[{"propuestas":"[]"}])[0])


if __name__ == "__main__":
    unittest.main()
