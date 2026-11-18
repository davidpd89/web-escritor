"""R5-7c: la alarma salta con un commit sembrado sin PR y con un check requerido que no está en verde."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bypass_usado as bu  # noqa: E402

REQ = {"Required merge gate", "lighthouse"}
SHA = "a" * 40


def pr(merge=SHA, base="main", merged=True):
    return {"number": 7, "merge_commit_sha": merge, "merged_at": "2026-11-16T00:00:00Z" if merged else None,
            "base": {"ref": base}, "head": {"sha": "h" * 40}}


class EvaluarTests(unittest.TestCase):
    def test_green_pr_merge_is_ok(self):
        self.assertEqual(bu.evaluar(SHA, [pr()], REQ, {"Required merge gate": "success", "lighthouse": "skipped"}), [])

    def test_seeded_commit_without_pr_fires(self):
        self.assertIn("no es el commit de fusión", bu.evaluar(SHA, [], REQ, {})[0])

    def test_commit_that_only_belongs_to_a_pr_is_not_its_merge(self):
        # un push directo de un commit que aparece en una PR (sin ser su fusión) sigue siendo bypass
        for otro in (pr(merge="b" * 40), pr(base="develop"), pr(merged=False)):
            with self.subTest(otro=otro):
                self.assertTrue(bu.evaluar(SHA, [otro], REQ, {"Required merge gate": "success", "lighthouse": "success"}))

    def test_red_or_missing_required_check_fires(self):
        motivos = bu.evaluar(SHA, [pr()], REQ, {"Required merge gate": "failure"})
        self.assertEqual(len(motivos), 2)
        self.assertTrue(any("failure" in m for m in motivos) and any("ausente" in m for m in motivos))

    def test_non_required_checks_are_ignored(self):
        res = {"Required merge gate": "success", "lighthouse": "success", "opcional": "failure"}
        self.assertEqual(bu.evaluar(SHA, [pr()], REQ, res), [])


if __name__ == "__main__":
    unittest.main()
