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
