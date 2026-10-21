"""Pruebas offline de extracción de JSON-LD Book desde ficha editorial."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reading_editorial_metadata import extract_books


def make_html(nodes):
    return ("<html><head><script type='application/ld+json'>"
            + json.dumps({"@context": "https://schema.org", "@graph": nodes},
                         ensure_ascii=False)
            + "</script></head><body><h1>Página editorial</h1></body></html>")


class EditorialMetadataTests(unittest.TestCase):
    def test_extract_exact_isbn_book(self):
        nodes = [
            {"@type": "BreadcrumbList", "itemListElement": []},
            {"@type": ["Book", "Product"], "isbn": "978-84-9838-237-2",
             "name": "Coraline", "author": {"@type": "Person", "name": "Neil Gaiman"},
             "publisher": {"@type": "Organization", "name": "Salamandra"},
             "datePublished": "2009-06-01",
             "image": [{"url": "https://editorial.example/media/coraline.jpg"}]},
        ]
        books = extract_books(make_html(nodes), "https://editorial.example/libro/coraline",
                              expected_isbn="9788498382372")
        self.assertEqual(len(books), 1)
        book = books[0]
        self.assertEqual(book["isbn13"], "9788498382372")
        self.assertEqual(book["autores"], ["Neil Gaiman"])
        self.assertEqual(book["precision_fecha"], "dia")
        self.assertEqual(book["portada_fuente_url"], "https://editorial.example/media/coraline.jpg")

    def test_never_accept_another_edition_or_product_only(self):
        nodes = [
            {"@type": "Product", "isbn": "9788498382372", "name": "No es Book",
             "author": "Neil Gaiman"},
            {"@type": "Book", "isbn": "9788498382372", "name": "Coraline",
             "author": "Neil Gaiman"},
            {"@type": "Book", "isbn": "9788412345674", "name": "Otra edición",
             "author": "Neil Gaiman"}
        ]
        books = extract_books(make_html(nodes), "https://editorial.example/ficha",
                              expected_isbn="9788498382372")
        self.assertEqual([b["titulo"] for b in books], ["Coraline"])

    def test_partial_date_unknown_image_does_not_invent_data(self):
        nodes = [{"@type": "Book", "isbn": "9788498382372",
                  "name": "Coraline", "author": ["Neil Gaiman"],
                  "datePublished": "2009", "image": "http://insecure.example/cover.jpg"}]
        books = extract_books(make_html(nodes), "https://editorial.example/ficha")
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]["precision_fecha"], "anio")
        self.assertIsNone(books[0]["portada_fuente_url"])

    def test_invalid_scripts_are_ignored(self):
        markup = ("<script type='application/ld+json'>this is not JSON</script>"
                  + make_html([{"@type": "Book", "name": "Sin ISBN",
                                "author": "Anónimo"}]))
        self.assertEqual(extract_books(markup, "https://editorial.example/ficha"), [])

    def test_url_and_isbn_validation(self):
        with self.assertRaises(ValueError):
            extract_books("", "http://editorial.example")
        with self.assertRaises(ValueError):
            extract_books("", "https://editorial.example/ficha", expected_isbn="no")

if __name__ == "__main__":
    unittest.main()
