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

    def test_canonical_author_order_without_wrong_author_collision(self):
        self.assertTrue(ratings.author_matches("Pérez Reverte Arturo", "Arturo Pérez Reverte"))
        self.assertTrue(ratings.author_matches("Neil Gaiman", "Neil Gaiman"))
        self.assertFalse(ratings.author_matches("Neil Otro", "Neil Gaiman"))
        self.assertFalse(ratings.author_matches("Ana María", "María Luisa"))

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

    def test_hardcover_aggregate_matches_exact_edition_and_author(self):
        response = {"data": {"editions": [{
            "isbn_13": "9788498382372", "isbn_10": None,
            "book": {"title": "Coraline", "slug": "coraline",
                     "rating": 4.36, "ratings_count": 1240,
                     "contributions": [{"contribution": "Author",
                                         "author": {"name": "Neil Gaiman"}}]}}
        ]}}
        record = ratings.select_hardcover_rating(BOOKS[0], response)
        self.assertEqual(record["puntuacion"], 4.36)
        self.assertEqual(record["numero_valoraciones"], 1240)
        self.assertEqual(record["fuente"], "hardcover")
        self.assertEqual(record["url"], "https://hardcover.app/books/coraline")
        response["data"]["editions"][0]["book"]["contributions"][0]["author"]["name"] = "Otra persona"
        self.assertIsNone(ratings.select_hardcover_rating(BOOKS[0], response))
        response["data"]["editions"][0]["book"]["contributions"][0]["author"]["name"] = "Neil Gaiman"
        response["data"]["editions"][0]["isbn_13"] = "9788425374012"
        self.assertIsNone(ratings.select_hardcover_rating(BOOKS[0], response))

    def test_hardcover_and_google_books_keep_independent_averages(self):
        market = {"schema_version": 1, "offers": [], "ratings": [{
            "fuente": "google_books", "libro_id": "lib-0001",
            "puntuacion": 3.7, "numero_valoraciones": 8,
            "url": "https://books.google.com/books?id=abc",
            "actualizado_en": "2026-10-20T10:00:00Z",
            "caduca_en": "2026-10-27T10:00:00Z"}]}
        response = {"data": {"editions": [{
            "isbn_13": "9788498382372",
            "book": {"title": "Coraline", "slug": "coraline",
                     "rating": 4.4, "ratings_count": 300,
                     "contributions": [{"author": {"name": "Neil Gaiman"}}]}}]}}
        out, stats = ratings.refresh({"libros": BOOKS}, market,
            lambda isbn: response if isbn == "9788498382372" else {"data": {"editions": []}},
            now=datetime(2026,10,21,10,tzinfo=timezone.utc), budget=2,
            source="hardcover")
        self.assertEqual(stats["updated"], 1)
        self.assertEqual(len(out["ratings"]), 2)
        self.assertEqual({r["fuente"] for r in out["ratings"]},
                         {"hardcover", "google_books"})

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
        self.assertEqual(result["ratings"][1]["caduca_en"], "2026-11-20T10:00:00Z")

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

    def test_unrated_books_are_queued_before_rated_ones(self):
        rated = {"libro_id": "lib-0001", "fuente": "google_books",
                 "puntuacion": 4.2, "numero_valoraciones": 16,
                 "url": "https://books.google.com/books?id=x",
                 "actualizado_en": "2026-10-20T10:00:00Z",
                 "caduca_en": "2026-11-19T10:00:00Z"}
        calls = []
        def provider(isbn):
            calls.append(isbn)
            return {"items": []}
        for day in range(1, 8):
            calls.clear()
            ratings.refresh({"libros": BOOKS}, {"ratings": [rated]}, provider,
                now=datetime(2026, 10, day, tzinfo=timezone.utc), budget=1)
            self.assertEqual(calls, ["9788425371967"])

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
