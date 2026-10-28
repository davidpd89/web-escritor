#!/usr/bin/env python3
"""Alimentador de Wikidata del Atlas: filtros de calidad, límites y fusión con el catálogo; sin red."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


feed = load("atlas_wikidata_feed", "scripts/atlas_wikidata_feed.py")
builder = load("build_atlas_pages", "scripts/build-atlas-pages.py")


def row(qid="Q100", label="Librería Prueba", city="Madrid", website="https://libreria.example/", coord="Point(-3.7 40.4)", links="9", desc=""):
    return {
        "item": {"value": f"http://www.wikidata.org/entity/{qid}"}, "itemLabel": {"value": label},
        "cityLabel": {"value": city}, "website": {"value": website}, "coord": {"value": coord},
        "sitelinks": {"value": links}, "itemDescription": {"value": desc},
    }


class FeedTest(unittest.TestCase):
    def test_row_filters(self) -> None:
        good = feed.parse_row(row(), "bookshop", "ES", 3)
        self.assertEqual((good["qid"], good["latitude"], good["longitude"]), ("Q100", 40.4, -3.7))
        for bad in (
            row(website="http://insegura.example/"), row(website="https://bit.ly/x"), row(website="https://127.0.0.1/"),
            row(website="https://u:p@libreria.example/"), row(coord="nonsense"), row(coord="Point(500 40)"),
            row(label="Q12345"), row(city="Q42"), row(links="1"), row(label="x" * 200), row(city=""),
        ):
            self.assertIsNone(feed.parse_row(bad, "bookshop", "ES", 3), bad)

    def test_collect_survives_failed_queries_and_dedupes(self) -> None:
        calls = []

        def query(text):
            calls.append(text)
            if "Q7075" in text:
                raise urllib.error.URLError("caída simulada")
            return {"results": {"bindings": [row(links="5"), row(links="12"), row(qid="Q101", label="Otra")]}}

        config = {"min_sitelinks": 3, "limit_per_query": 5, "delay_seconds": 0, "countries": ["ES"],
                  "kinds": [{"place_type": "bookshop", "qid": "Q200764"}, {"place_type": "library", "qid": "Q7075"}]}
        found, errors = feed.collect(config, query_fn=query, sleep=lambda _: None)
        self.assertEqual(len(calls), 2)
        self.assertEqual(errors, ["library/ES: URLError"])
        self.assertEqual([e["qid"] for e in found], ["Q100", "Q101"])
        self.assertEqual(found[0]["sitelinks"], 12)

    def test_merge_caps_new_entries_and_expires_old_ones(self) -> None:
        old = {"places": [
            {"qid": "Q1", "name": "Vista", "city": "A", "country_iso2": "ES", "place_type": "library", "sitelinks": 9, "last_seen": "2026-10-20", "first_seen": "2026-10-01"},
            {"qid": "Q2", "name": "Caducada", "city": "A", "country_iso2": "ES", "place_type": "library", "sitelinks": 9, "last_seen": "2026-08-01", "first_seen": "2026-08-01"},
        ]}
        fresh = [{"qid": f"Q{n}", "name": f"N{n}", "city": "B", "country_iso2": "ES", "place_type": "bookshop", "sitelinks": 5} for n in range(10, 15)]
        merged = feed.merge(old, fresh, "2026-10-28", {"keep_days": 30, "max_new_per_run": 3})
        qids = {p["qid"] for p in merged["places"]}
        self.assertIn("Q1", qids)
        self.assertNotIn("Q2", qids)
        self.assertEqual(len([q for q in qids if q.startswith("Q1") and len(q) == 3]), 3)

    def test_retry_honours_retry_after(self) -> None:
        waits = []
        attempts = {"n": 0}

        class Response:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b'{"results": {"bindings": []}}'

        original = feed.urllib.request.urlopen

        def fake(request, timeout=0):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise urllib.error.HTTPError(request.full_url, 429, "Too Many Requests", {"Retry-After": "7"}, None)
            return Response()

        feed.urllib.request.urlopen = fake
        try:
            self.assertEqual(feed.run_query("SELECT 1", sleep=waits.append), {"results": {"bindings": []}})
        finally:
            feed.urllib.request.urlopen = original
        self.assertEqual(attempts["n"], 3)
        self.assertTrue(all(w >= 7 for w in waits) and len(waits) == 2)


class DirectoryMergeTest(unittest.TestCase):
    def test_directory_entries_become_valid_contract_places(self) -> None:
        catalogue = json.loads((ROOT / "data/atlas/catalogue.json").read_text(encoding="utf-8"))
        directory = {"updated": "2026-10-28", "places": [
            {"qid": "Q1001", "name": "Biblioteca Prueba", "city": "Dublín", "country_iso2": "IE", "place_type": "library",
             "official_url": "https://biblioteca.example/", "latitude": 53.3, "longitude": -6.2, "sitelinks": 20, "description": ""},
            {"qid": "Q1002", "name": "Librería Nueva", "city": "Valparaíso", "country_iso2": "CL", "place_type": "bookshop",
             "official_url": "https://nueva.example/", "latitude": -33.0, "longitude": -71.6, "sitelinks": 7, "description": "librería en Chile"},
        ]}
        merged = builder.merge_directory(catalogue, directory, {})
        self.assertEqual(builder._contract.problems(merged), [])
        ids = {d["id"]: d for d in merged["destinations"]}
        self.assertIn("dublin", ids)  # reutiliza el destino editorial
        self.assertIn("valparaiso", ids)
        new = next(p for p in merged["places"] if p["id"] == "wd-q1001")
        self.assertEqual(new["destination_id"], "dublin")
        self.assertEqual(len(catalogue["places"]) + 2, len(merged["places"]))
        # Una segunda fusión con la misma web oficial no duplica
        again = builder.merge_directory(merged, directory, {})
        self.assertEqual(len(again["places"]), len(merged["places"]))


if __name__ == "__main__":
    unittest.main()
