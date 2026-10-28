#!/usr/bin/env python3
"""El Atlas publicado se genera desde el dataset y respeta el contrato de publicación."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "atlas-pages.json"
PERMITTED_LABELS = {"hecho", "tradicion", "atribucion", "ficcion"}


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)


class AtlasPagesTest(unittest.TestCase):
    def test_generated_output_is_current(self) -> None:
        result = run("scripts/build-atlas-pages.py", "--data", "data/atlas-pages.json", "--root", ".", "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_contract_passes(self) -> None:
        result = run("scripts/check_atlas_release_contract.py", "--root", ".", "--manifest", "data/atlas-routes-manifest.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_fact_is_labelled_and_sourced(self) -> None:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["entries"]), 6)
        for entry in data["entries"]:
            self.assertTrue(entry["sources"], entry["slug"])
            for fact in entry["facts"]:
                self.assertIn(fact["label"], PERMITTED_LABELS, entry["slug"])
            self.assertTrue(any(f["label"] == "hecho" for f in entry["facts"]), entry["slug"])

    def test_atlas_is_in_registry_navigation_and_public_namespace(self) -> None:
        registry = json.loads((ROOT / "data" / "content-registry.json").read_text(encoding="utf-8"))
        urls = {e["url"] for e in registry["entries"]}
        data = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertIn("/atlas-literario/", urls)
        for entry in data["entries"]:
            self.assertIn(f"/atlas-literario/{entry['slug']}/", urls)
        nav = json.loads((ROOT / "data" / "navigation.json").read_text(encoding="utf-8"))
        self.assertIn("atlas-hub", nav["footer"]["Leer y recursos"])
        self.assertIn("atlas-hub", [i["targetId"] for i in nav["menu"]["recommendations-hub"]])
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://davidportodiaz.com/atlas-literario/", sitemap)
        self.assertIn('"atlas-literario/"', (ROOT / "scripts" / "build-public-dist.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
