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

    def test_roles_are_not_part_of_the_name(self):
        self.assertEqual(split_authors(["(Ed.) Jose Rico Paves"]), ["Jose Rico Paves"])
        self.assertEqual(split_authors(["Ana Gil (coord.)"]), ["Ana Gil"])
        self.assertEqual(split_authors(["Luis Paz (trad.) / Eva Mar"]), ["Luis Paz", "Eva Mar"])
        self.assertEqual(split_authors(["Marta Ruiz, editora"]), ["Marta Ruiz"])
        self.assertEqual(split_authors(["Patri Psicóloga (Patri Psicóloga)"]), ["Patri Psicóloga"])
        # Un seudónimo distinto entre paréntesis es información del autor y se conserva.
        self.assertEqual(split_authors(["Laura Álvarez (La pediatra Laura)"]), ["Laura Álvarez (La pediatra Laura)"])
        self.assertEqual(split_authors(["Eduardo Mendoza"]), ["Eduardo Mendoza"])  # «Ed» al inicio de un nombre

    def test_collective_names_have_one_form(self):
        for raw in ("V. Autores", "AA. VV.", "VV.AA.", "Varios", "varios autores"):
            self.assertEqual(split_authors([raw]), ["Varios autores"], raw)
        self.assertEqual(split_authors(["ANÓNIMO"]), ["Anónimo"])
        self.assertEqual(split_authors(["Ana Varios"]), ["Ana Varios"])

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
            self.assertFalse((ROOT / record["url"].strip("/") / "index.html").exists(), record["url"])
            for heir in record["sustituidaPor"]:
                self.assertIn(heir.strip("/").split("/")[-1], slugs, heir)
                self.assertTrue((ROOT / heir.strip("/") / "index.html").exists(), heir)

    def test_retired_page_is_removed_only_when_the_retirement_is_recorded(self):
        import importlib.util
        import tempfile

        spec = importlib.util.spec_from_file_location("normalize_authors", ROOT / "scripts/normalize-reading-authors.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for slug in ("con-sustituta", "sin-sustituta"):
                page = root / "recomendaciones/autores" / slug / "index.html"
                page.parent.mkdir(parents=True)
                page.write_text("<html></html>", encoding="utf-8")
            retired = [{"slug": "con-sustituta"}, {"slug": "sin-sustituta"}]
            removed = module.remove_retired_pages(retired, {"/recomendaciones/autores/con-sustituta/"}, root)
            self.assertEqual(removed, ["/recomendaciones/autores/con-sustituta/"])
            self.assertFalse((root / "recomendaciones/autores/con-sustituta").exists())
            self.assertTrue((root / "recomendaciones/autores/sin-sustituta/index.html").exists())


if __name__ == "__main__":
    unittest.main()
