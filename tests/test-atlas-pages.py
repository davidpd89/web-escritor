#!/usr/bin/env python3
"""El Atlas publicado se genera desde el dataset y respeta el contrato de publicación."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "atlas" / "editorial.json"
PERMITTED_LABELS = {"hecho", "tradicion", "atribucion", "ficcion"}


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)


class AtlasPagesTest(unittest.TestCase):
    def test_generated_output_is_current(self) -> None:
        result = run("scripts/build-atlas-pages.py", "--data", "data/atlas/catalogue.json", "--root", ".", "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_contract_passes(self) -> None:
        result = run("scripts/check_atlas_release_contract.py", "--root", ".", "--manifest", "data/atlas-routes-manifest.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_fact_is_labelled_and_sourced(self) -> None:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["pages"]), 6)
        for slug, entry in data["pages"].items():
            self.assertTrue(entry["sources"], slug)
            for fact in entry["facts"]:
                self.assertIn(fact["label"], PERMITTED_LABELS, slug)
            self.assertTrue(any(f["label"] == "hecho" for f in entry["facts"]), slug)

    def test_atlas_is_in_registry_navigation_and_public_namespace(self) -> None:
        registry = json.loads((ROOT / "data" / "content-registry.json").read_text(encoding="utf-8"))
        urls = {e["url"] for e in registry["entries"]}
        data = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertIn("/atlas-literario/", urls)
        for slug in data["pages"]:
            self.assertIn(f"/atlas-literario/{slug}/", urls)
        nav = json.loads((ROOT / "data" / "navigation.json").read_text(encoding="utf-8"))
        self.assertIn("atlas-hub", nav["footer"]["Leer y recursos"])
        self.assertIn("atlas-hub", [i["targetId"] for i in nav["menu"]["recommendations-hub"]])
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://davidportodiaz.com/atlas-literario/", sitemap)
        self.assertIn('"atlas-literario/"', (ROOT / "scripts" / "build-public-dist.py").read_text(encoding="utf-8"))

    def test_hub_lists_every_approved_place_and_hides_unverified_claims(self) -> None:
        catalogue = json.loads((ROOT / "data" / "atlas" / "catalogue.json").read_text(encoding="utf-8"))
        hub = (ROOT / "atlas-literario" / "index.html").read_text(encoding="utf-8")
        for place in catalogue["places"]:
            if place["status"] == "approved":
                self.assertIn(place["name"].replace("'", "&#x27;"), hub, place["id"])
        # Una asociación popular sin verificar nunca llega a la ficha pública del catálogo.
        molinos = next(c for c in hub.split("<li ") if 'data-title="Molinos de Campo de Criptana"' in c)
        self.assertIn('data-obra=""', molinos)
        self.assertNotIn("Aparece en la obra", molinos)
        self.assertNotIn("popular_claim", hub)
        for facet in ("pais", "destino", "tipo", "vinculo", "obra", "autor", "visita"):
            self.assertIn(f'data-facet-group="{facet}"', hub)

    def test_every_page_in_manifest_is_in_the_catalogue_data(self) -> None:
        editorial = json.loads(DATA.read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "data" / "atlas-routes-manifest.json").read_text(encoding="utf-8"))
        urls = {r["url"] for r in manifest["routes"]}
        self.assertEqual(urls, {"/atlas-literario/"} | {f"/atlas-literario/{s}/" for s in editorial["pages"]})


if __name__ == "__main__":
    unittest.main()
