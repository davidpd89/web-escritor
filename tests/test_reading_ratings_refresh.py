"""Offline tests for official Google Books ratings, keyed to exact book edition."""
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reading_ratings_refresh",
    ROOT / "scripts/reading_ratings_refresh.py")
ratings = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ratings
spec.loader.exec_module(ratings)


def volume(identifier="9788498382372", title="Coraline", author="Neil Gaiman",
           rating=4.1, count=320, volume_id="sAfGx_abc"):
    return {"id": volume_id, "volumeInfo": {
        "title": title, "authors": [author],
        "industryIdentifiers": [{"type": "ISBN_13", "identifier": identifier}],
        "averageRating": rating, "ratingsCount": count,
        "language": "es"
    }}


BOOKS = [
    {"id": "lib-0001", "titulo": "Coraline",
     "autores": ["Neil Gaiman"], "isbn13": "9788498382372", "estado": "publicado"},
    {"id": "lib-0002", "titulo": "Libro sin votos",
     "autores": ["Autora de prueba"], "isbn13": "9788425371967", "estado": "publicado"},
    {"id": "lib-0003", "titulo": "No publicado",
     "autores": ["Autor de prueba"], "isbn13": "9788425374012", "estado": "borrador"},
]


class GoogleRatingsTests(unittest.TestCase):
    def test_valid_isbn_and_ratings(self):
        self.assertEqual(ratings.isbn13("978-84-9838-237-2"), "9788498382372")
        self.assertIsNone(ratings.isbn13("9788498382373"))
        record = ratings.select_rating(BOOKS[0], {"items": [volume()]})
        self.assertEqual(record["puntuacion"], 4.1)
        self.assertEqual(record["numero_valoraciones"], 320)
        self.assertEqual(record["fuente"], "google_books")
        self.assertEqual(record["url"], "https://books.google.com/books?id=sAfGx_abc")

    def test_wrong_isbn_title_author_and_noratings_are_rejected(self):
        variants = [
            volume(identifier="9788425374012"),
            volume(title="Un libro totalmente distinto"),
            volume(author="Otra persona"),
            volume(rating=None),
            volume(count=0),
            volume(count=True),
            volume(volume_id="https://malicious.example/abc"),
        ]
        for sample in variants:
            with self.subTest(sample=sample):
                self.assertIsNone(ratings.select_rating(BOOKS[0], {"items": [sample]}))

    def test_rating_prefers_more_votes_not_first_result(self):
        a, b = volume(rating=4.2, count=21, volume_id="valid_1"), volume(
            rating=3.9, count=100, volume_id="valid_2")
        record = ratings.select_rating(BOOKS[0], {"items": [a, b]})
        self.assertEqual(record["puntuacion"], 3.9)
        self.assertEqual(record["numero_valoraciones"], 100)

    def test_bounded_refresh_keeps_goodreads_legacy_and_unrated_clean(self):
        market = {"schema_version": 1, "offers": [], "ratings": [
            {"libro_id": "lib-0001", "url": "https://www.goodreads.com/book/show/6785288.Coraline",
             "puntuacion": 4.13, "numero_valoraciones": 800000,
             "actualizado_en": "2026-10-20T12:00:00Z", "caduca_en": "2026-10-27T12:00:00Z"}
        ]}
        calls = []
        def provider(isbn):
            calls.append(isbn)
            return {"items": [volume()]} if isbn == "9788498382372" else {"items": []}
        result, stats = ratings.refresh({"libros": BOOKS}, market, provider,
             now=datetime(2026,10,21,10,0,tzinfo=timezone.utc), budget=2)
        self.assertEqual(stats["attempted"], 2)
        self.assertEqual(stats["updated"], 1)
        self.assertEqual(stats["unrated"], 1)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(result["ratings"]), 2)
        self.assertEqual(result["ratings"][0], market["ratings"][0])
        self.assertEqual(result["ratings"][1]["fuente"], "google_books")
        self.assertEqual(result["ratings"][1]["caduca_en"], "2026-10-28T10:00:00Z")

    def test_failures_do_not_replace_previous_data_or_expand_budget(self):
        old = {"libro_id": "lib-0001", "fuente": "google_books",
               "puntuacion": 4.2, "numero_valoraciones": 16,
               "url": "https://books.google.com/books?id=x",
               "actualizado_en": "2026-10-19T10:00:00Z",
               "caduca_en": "2026-10-26T10:00:00Z"}
        def failing(_isbn):
            raise RuntimeError("HTTP 429")
        market = {"schema_version": 1, "offers": [], "ratings": [old]}
        result, stats = ratings.refresh({"libros": BOOKS}, market, failing,
            now=datetime(2026,10,21,tzinfo=timezone.utc), budget=1)
        self.assertEqual(stats["attempted"], 1)
        self.assertEqual(len(stats["failures"]), 1)
        self.assertEqual(result["ratings"], [old])
        self.assertEqual(stats["updated"], 0)

    def test_no_network_is_required_for_fixture_and_changed_writes_only(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "ratings.json"
            doc = {"schema_version": 1, "offers": [], "ratings": []}
            self.assertTrue(ratings.write_changed(p, doc))
            last = p.stat().st_mtime_ns
            self.assertFalse(ratings.write_changed(p, doc))
            self.assertEqual(last, p.stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
