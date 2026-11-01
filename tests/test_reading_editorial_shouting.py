"""Titulares en mayúsculas, citas de prensa y autores en mayúsculas de las fuentes editoriales."""
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reading_intake_core import clean_author, strip_shouting  # noqa: E402

PLOT = "Tiene siete años y ya conoce el hambre. En la noche polar, su madre ablanda la cuerda."


class StripShoutingTests(unittest.TestCase):
    def test_leading_taglines_and_press_quotes_go_away(self):
        self.assertEqual(strip_shouting("UNA PRECIOSA NOVELA QUE NOS LLEVA A GROENLANDIA " + PLOT), PLOT)
        self.assertEqual(strip_shouting("TODA LEYENDA TIENE UN ORIGEN. «El maestro de la novela histórica.» "
                                        "The Washington Post UN MATRIMONIO BENDECIDO CON LA SANGRE " + PLOT), PLOT)
        self.assertEqual(strip_shouting("LA NOVELA DEBUT MÁS VENDIDA DEL AÑO «¡Doce estrellas!» LISA JEWEL "
                                        "UN PUEBLO PEQUEÑO. UN CRIMEN ATROZ. " + PLOT), PLOT)

    def test_inner_shouting_is_lowercased_not_lost(self):
        self.assertEqual(strip_shouting("Un libro de crianza para quienes quieren criar en EQUIPO DE VERDAD. Criar a un hijo no viene con instrucciones."),
                         "Un libro de crianza para quienes quieren criar en equipo de verdad. Criar a un hijo no viene con instrucciones.")
        self.assertEqual(strip_shouting("Una novela que transforma lo íntimo en universal. SIEMPRE ES POSIBLE RECUPERAR LA FELICIDAD Luca, de catorce años, vive junto al mar."),
                         "Una novela que transforma lo íntimo en universal. Siempre es posible recuperar la felicidad. Luca, de catorce años, vive junto al mar.")
        self.assertIn("sencilla: si la receta no se prepara en 20 minutos, no entra",
                      strip_shouting("La promesa es sencilla: SI LA RECETA NO SE PREPARA EN 20 MINUTOS, NO ENTRA EN ESTE LIBRO. Con diez ingredientes."))

    def test_acronyms_normal_text_and_short_leftovers_are_untouched(self):
        for text in ("La ONU y la OTAN firmaron en EEUU un acuerdo que cambió la política de toda Europa.", PLOT):
            self.assertEqual(strip_shouting(text), text)
        self.assertEqual(strip_shouting("EL GRAN LIBRO DEL AÑO Corto."), "EL GRAN LIBRO DEL AÑO Corto.")


class CleanAuthorTests(unittest.TestCase):
    def test_all_caps_names_become_proper_names(self):
        self.assertEqual(clean_author("JØRN LIER HORST"), "Jørn Lier Horst")
        self.assertEqual(clean_author("MARÍA DE LA O"), "María de la O")
        self.assertEqual(clean_author("JEAN-PAUL SARTRE"), "Jean-Paul Sartre")

    def test_styled_pseudonyms_and_normal_names_stay(self):
        for name in ("KKAM", "Ali Smith", "J. R. R. Tolkien", "Alana S. Portero"):
            self.assertEqual(clean_author(name), name)


class PublishedCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("builder", ROOT / "scripts/build-reading-catalogue.py")
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)
        cls.data = json.loads((ROOT / "data/reading-catalogue.json").read_text(encoding="utf-8"))

    def test_no_meta_description_or_card_opens_with_a_shouted_tagline(self):
        shout = re.compile(r"^(?:\S*[A-ZÁÉÍÓÚÑ]{2,}\S*\s+){3}")
        for b in self.data["libros"]:
            if b["estado"] != "publicado":
                continue
            for text in (self.builder.meta_synopsis(b), self.builder.card_synopsis(b)):
                self.assertIsNone(shout.match(text), (b["id"], text[:80]))

    def test_no_published_author_is_written_in_capitals(self):
        names = {a for b in self.data["libros"] for a in b["autores"]}
        self.assertEqual({a for a in names if clean_author(a) != a}, set())


if __name__ == "__main__":
    unittest.main()
