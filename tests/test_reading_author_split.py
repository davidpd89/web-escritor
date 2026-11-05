import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reading_intake_core import split_authors  # noqa: E402


class AuthorSplitTest(unittest.TestCase):
    def test_several_people_in_one_string(self):
        self.assertEqual(split_authors(["Cristian Morales / Javier González Alcázar"]), ["Cristian Morales", "Javier González Alcázar"])
        self.assertEqual(split_authors(["Itziar Miranda y Jorge Miranda"]), ["Itziar Miranda", "Jorge Miranda"])
        self.assertEqual(split_authors(["Lucía Ruiz Lafita, Delirium"]), ["Lucía Ruiz Lafita", "Delirium"])
        self.assertEqual(split_authors(["Ana López; Luis Gil"]), ["Ana López", "Luis Gil"])

    def test_handles_and_repeated_names(self):
        self.assertEqual(split_authors(["Úrsula Perona @ursulaperonapsicologa"]), ["Úrsula Perona"])
        self.assertEqual(split_authors(["Pablo R. Coca (@occimorons)"]), ["Pablo R. Coca"])
        self.assertEqual(split_authors(["Hyūga Natsu Hyuganatsu / Touko Shino"]), ["Hyūga Natsu", "Touko Shino"])
        self.assertEqual(split_authors(["Ana López", "ANA LÓPEZ"]), ["Ana López"])

    def test_single_names_stay_whole(self):
        for name in ("Santiago Ramón y Cajal", "José Ortega y Gasset", "García Márquez, Gabriel",
                     "Moderna de Pueblo", "Enrique López López", "Alaa al Aswani", "KKAM"):
            self.assertEqual(split_authors([name]), [name])
        self.assertEqual(split_authors(["JØRN LIER HORST"]), ["Jørn Lier Horst"])

    def test_idempotent(self):
        names = ["Soumaya Keynes y Chad P. Bown", "Marcos Serén @chefmspin.recetas"]
        self.assertEqual(split_authors(split_authors(names)), split_authors(names))

    def test_published_catalogue_has_one_person_per_author(self):
        result = subprocess.run([sys.executable, "scripts/normalize-reading-authors.py", "--check"], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_retired_profiles_point_to_existing_heirs(self):
        # El control de enlaces acepta la baja de una ficha solo si sus herederas existen.
        retired = json.loads((ROOT / "data/reading-author-retirements.json").read_text(encoding="utf-8"))
        slugs = {a["slug"] for a in json.loads((ROOT / "data/reading-authors.json").read_text(encoding="utf-8"))["autores"]}
        for record in retired["retiradas"]:
            old = record["url"].strip("/").split("/")[-1]
            self.assertNotIn(old, slugs, record["url"])
            self.assertTrue(record["sustituidaPor"], record["url"])
            for heir in record["sustituidaPor"]:
                self.assertIn(heir.strip("/").split("/")[-1], slugs, heir)
                self.assertTrue((ROOT / heir.strip("/") / "index.html").exists(), heir)


if __name__ == "__main__":
    unittest.main()
