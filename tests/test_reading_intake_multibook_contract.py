"""Contrato del motor web actual con más de un libro (fixtures aisladas).

No publica páginas, no usa Amazon/API/LLM y no altera data/reading-catalogue.json.
Basado en el generador ya fusionado en PR #660.
"""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reading_catalogue_contract", ROOT / "scripts/build-reading-catalogue.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

ISBN = ["9780140328721", "9780140449136", "9788498382372"]
TITLES = ["Primer libro de prueba", "Segundo libro de prueba", "Tercer libro de prueba"]


class MultiBookContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "assets/reading-covers").mkdir(parents=True, exist_ok=True)
        (self.root / "editoriales/salamandra").mkdir(parents=True, exist_ok=True)
        (self.root / "editoriales/salamandra/index.html").write_text("<!doctype html>", encoding="utf-8")
        original = json.loads((ROOT / "data/reading-catalogue.json").read_text(encoding="utf-8"))
        self.data = {"schema_version": 1, "categorias": original["categorias"],
                     "libros": [], "libro_categorias": []}
        source = original["libros"][0]
        for i in range(3):
            b = copy.deepcopy(source)
            b.pop("amazon_busqueda_isbn", None)  # el contrato exige que coincida con el ISBN de cada ficha
            b.update({
                "id": f"contrato-{i+1:03}",
                "slug": f"obra-tecnica-{i+1:03}",
                "titulo": TITLES[i],
                "autores": [f"Autor de prueba {i+1}"],
                "isbn13": ISBN[i],
                "descripcion_breve": (
                    f"Descripción original y distinta del libro de prueba {i+1}; "
                    "contiene información editorial suficiente para el contrato técnico."
                ),
                "edicion": f"Edición ficticia de prueba {i+1}, nunca publicable",
                "portada_local": f"/assets/reading-covers/prueba-{i+1}.png",
                "portada_ancho": 120, "portada_alto": 180,
                "portada_fuente_url": f"https://example.org/portadas/prueba-{i+1}",
                "fuente_bibliografica_url": f"https://example.org/ficha/prueba-{i+1}",
                "fecha_publicacion": "2026-10-12",
                "fuente_publicacion_url": f"https://example.org/fecha/prueba-{i+1}",
                "fecha_actualizacion": "2026-10-20",
                "fecha_verificacion": "2026-10-20",
                "portada_fecha_revision": "2026-10-20",
                "url_amazon_afiliada": f"https://www.amazon.es/dp/B00000000{i+1}?tag=davidporto-21",
                "formatos_compra": [
                    {"formato": "ebook",
                     "url": f"https://www.amazon.es/dp/B00000000{i+1}?tag=davidporto-21",
                     "fuente_url": f"https://example.org/ebook/{i+1}",
                     "fecha_verificacion": "2026-10-20"}
                ],
            })
            for optional in ("audio_descripcion", "audio_voz", "resenas",
                             "fragmento_url", "edad_recomendada", "fuente_edad_url"):
                b.pop(optional, None)
            Image.new("RGB", (120, 180), (40 + i * 50, 80, 120)).save(
                self.root / b["portada_local"].lstrip("/"))
            self.data["libros"].append(b)
            cats = ["fantasia-juvenil", "halloween"] if i == 0 else (
                ["romantasy", "fantasia"] if i == 1 else ["terror", "misterio-y-thriller"]
            )
            self.data["libro_categorias"].extend(
                {"libro_id": b["id"], "categoria_id": cat} for cat in cats
            )
        self.template = (ROOT / "scripts/templates/reading-catalogue.html.tmpl").read_text(encoding="utf-8")

    def test_three_independent_pages_one_hub_and_categories(self):
        books = builder.validate(self.data, self.root)
        self.assertEqual(len(books), 3)
        hub = builder.render_hub(self.data, books, self.template)
        self.assertEqual(hub.count("data-catalogue-book "), 3)
        for b in books:
            canonical = "https://davidportodiaz.com" + builder.url(b)
            html = builder.render_book(self.data, b, self.template)
            self.assertIn('<link rel="canonical" href="' + canonical + '"', html)
            self.assertIn(b["isbn13"], html)
            self.assertIn(b["titulo"], html)
            self.assertIn('data-purchase-format="ebook"', html)
            self.assertIn('rel="sponsored nofollow noopener noreferrer"', html)
            self.assertIn('href="' + b["url_amazon_afiliada"] + '"', html)
            self.assertNotIn("Segundo libro de prueba" if b["id"] == "contrato-001"
                             else "Primer libro de prueba", html)
        self.assertEqual(len({builder.url(b) for b in books}), 3)
        self.assertEqual(len(builder.registry_entries(books)), 3)

    def test_duplicate_work_even_different_isbn_is_rejected(self):
        other = copy.deepcopy(self.data)
        other["libros"][1]["titulo"] = other["libros"][0]["titulo"]
        other["libros"][1]["autores"] = other["libros"][0]["autores"]
        with self.assertRaises(builder.ValidationError):
            builder.validate(other, self.root)

    def test_missing_cover_does_not_silently_publish(self):
        bad = copy.deepcopy(self.data)
        bad["libros"][2]["portada_local"] = "/assets/reading-covers/ausente.png"
        with self.assertRaises(builder.ValidationError):
            builder.validate(bad, self.root)

    def test_partially_ready_book_does_not_break_other_two(self):
        data = copy.deepcopy(self.data)
        data["libros"][1]["estado"] = "borrador"
        books = builder.validate(data, self.root)
        self.assertEqual([b["id"] for b in books], ["contrato-001", "contrato-003"])


if __name__ == "__main__":
    unittest.main()
