"""R5-6: el deploy superpone la instantánea social más reciente y válida (rama social-estado o main)."""
from datetime import timedelta
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import social_estado as se  # noqa: E402
from test_gpt_social_publish import NOW, snapshot  # noqa: E402


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root, self.out = self.tmp / "repo", self.tmp / "dist"
        (self.root / se.pub.REL).parent.mkdir(parents=True)
        (self.out / se.pub.REL).parent.mkdir(parents=True)

    def go(self, rama, main):
        if main is not None:
            (self.root / se.pub.REL).write_text(main, encoding="utf-8")
            (self.out / se.pub.REL).write_text(main, encoding="utf-8")
        return se.superponer(self.out, rama, self.root)

    def built(self):
        return (self.out / se.pub.REL).read_text(encoding="utf-8")

    def test_newer_branch_snapshot_is_published(self):
        nueva = snapshot(150, NOW + timedelta(days=2))
        self.assertEqual(self.go(nueva, snapshot(100)), se.pub.BRANCH)
        self.assertEqual(self.built(), nueva)

    def test_older_branch_snapshot_never_replaces_main(self):
        main = snapshot(150, NOW + timedelta(days=2))
        self.assertEqual(self.go(snapshot(100), main), "main")
        self.assertEqual(self.built(), main)

    def test_invalid_or_missing_branch_falls_back_to_main(self):
        main = snapshot(100)
        for rama in (None, "", "{", snapshot(150).replace('"ok"', '"bogus"')):
            with self.subTest(rama=rama[:20] if rama else rama):
                self.assertEqual(self.go(rama, main), "main")
                self.assertEqual(self.built(), main)

    def test_expired_snapshot_still_wins_if_newest(self):
        # caducada respecto a hoy, pero más reciente que la de main: el panel ya muestra la caducidad
        nueva = snapshot(150, NOW - timedelta(days=300) + timedelta(days=1))
        self.assertEqual(self.go(nueva, snapshot(100, NOW - timedelta(days=300))), se.pub.BRANCH)
        self.assertEqual(self.built(), nueva)

    def test_tie_prefers_branch(self):
        self.assertEqual(self.go(snapshot(150), snapshot(100)), se.pub.BRANCH)

    def test_branch_only_without_main_copy(self):
        nueva = snapshot(150)
        self.assertEqual(self.go(nueva, None), se.pub.BRANCH)
        self.assertEqual(self.built(), nueva)


if __name__ == "__main__":
    unittest.main()
