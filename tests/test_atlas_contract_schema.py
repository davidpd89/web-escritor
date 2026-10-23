"""Draft 2020-12 validation of the atlas schema plus cross-layer regressions.

Offline. Needs `jsonschema` (installed by the atlas-contract workflow); skipped otherwise.
The Python gate and the schema are complementary: each mutation below states which
layer must reject it.
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("atlas_contract_check", ROOT / "scripts/atlas_contract_check.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
SCHEMA = json.loads((ROOT / "schemas/atlas/catalogue-v1.schema.json").read_text(encoding="utf-8"))
DAY = "2026-10-21"


def full():
    """Schema-valid, gate-valid, fully approved snapshot (the only baseline for mutations)."""
    return {
        "schema_version": 1,
        "destinations": [{"id": "dst-lisboa", "status": "approved", "verified_at": DAY, "slug": "lisboa",
                          "name": "Lisboa", "country_iso2": "PT", "summary_original": "Introducción propia"},
                         {"id": "dst-porto", "status": "approved", "verified_at": DAY, "slug": "porto",
                          "name": "Porto", "country_iso2": "PT"}],
        "places": [{"id": "lug-libreria", "status": "approved", "verified_at": DAY, "slug": "libreria",
                    "name": "Librería", "destination_id": "dst-lisboa", "place_type": "bookshop",
                    "geo_precision": "point", "latitude": 38.7, "longitude": -9.1,
                    "summary_original": "Texto propio", "source_ids": ["src-a"], "image_ids": ["img-a"]},
                   {"id": "lug-biblioteca", "status": "approved", "verified_at": DAY, "slug": "biblioteca",
                    "name": "Biblioteca", "destination_id": "dst-lisboa", "place_type": "library",
                    "geo_precision": "city", "summary_original": "Texto propio", "source_ids": ["src-a"]},
                   {"id": "lug-oporto", "status": "approved", "verified_at": DAY, "slug": "oporto",
                    "name": "Oporto", "destination_id": "dst-porto", "place_type": "library",
                    "geo_precision": "city", "summary_original": "Texto propio", "source_ids": ["src-a"]}],
        "works": [{"id": "obr-a", "status": "approved", "verified_at": DAY, "title": "T", "author_ids": ["aut-a"]}],
        "authors": [{"id": "aut-a", "status": "approved", "verified_at": DAY, "name": "A"}],
        "adaptations": [{"id": "ada-a", "status": "approved", "verified_at": DAY, "title": "Peli",
                         "media_type": "film", "original_work_id": "obr-a"}],
        "sources": [{"id": "src-a", "url": "https://example.org/x", "title": "t", "publisher": "p",
                     "retrieved_at": DAY, "source_kind": "other", "evidence_summary": "e",
                     "license_review": "pending"}],
        "relationships": [{"id": "rel-a", "place_id": "lug-libreria", "subject_type": "work",
                           "subject_id": "obr-a", "relationship_type": "narrative_explicit",
                           "source_ids": ["src-a"], "status": "approved", "evidence_note": "n",
                           "verified_at": DAY}],
        "images": [{"id": "img-a", "place_id": "lug-libreria", "source_url": "https://example.org/i",
                    "license": "CC BY 4.0", "license_url": "https://example.org/l", "attribution": "a",
                    "status": "approved"}],
        "routes": [{"id": "rou-a", "status": "approved", "verified_at": DAY, "slug": "ruta", "title": "Ruta",
                    "destination_id": "dst-lisboa", "place_ids": ["lug-libreria", "lug-biblioteca"]}],
    }


def drop_coordinates(d):
    d["places"][0].pop("latitude")
    d["places"][0].pop("longitude")


@unittest.skipIf(Draft202012Validator is None, "jsonschema no instalado")
class SchemaLayerTest(unittest.TestCase):
    validator = None

    @classmethod
    def setUpClass(cls):
        Draft202012Validator.check_schema(SCHEMA)
        cls.validator = Draft202012Validator(SCHEMA, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def schema_errors(self, data):
        return [e.message for e in self.validator.iter_errors(data)]

    def mutated(self, fn):
        data = full()
        fn(data)
        return data

    def test_baseline_valid_in_both_layers(self):
        self.assertEqual(self.schema_errors(full()), [])
        self.assertEqual(mod.problems(full()), [])

    def test_schema_rejects(self):
        cases = {
            "typo en campo de lugar": lambda d: d["places"][0].update(lattitude=1),
            "campo desconocido en ruta": lambda d: d["routes"][0].update(notas="x"),
            "fecha de calendario imposible": lambda d: d["sources"][0].update(retrieved_at="2026-13-45"),
            "aprobado sin verified_at": lambda d: d["works"][0].pop("verified_at"),
            "lugar aprobado sin resumen": lambda d: d["places"][0].pop("summary_original"),
            "lugar aprobado sin fuentes": lambda d: d["places"][0].update(source_ids=[]),
            "punto sin coordenadas": drop_coordinates,
            "latitud sin longitud": lambda d: d["places"][1].update(latitude=1.0),
            "unlocated con coordenadas": lambda d: d["places"][0].update(geo_precision="unlocated"),
            "osm_id sin osm_type": lambda d: d["places"][0].update(osm_id=5),
            "filming_location sobre una obra": lambda d: d["relationships"][0].update(relationship_type="filming_location"),
            "mito aprobado": lambda d: d["relationships"][0].update(relationship_type="popular_claim_unverified"),
            "relación aprobada sin verified_at": lambda d: d["relationships"][0].pop("verified_at"),
            "overture_confidence nulo": lambda d: d["places"][0].update(overture_confidence=None),
            "ruta de una parada": lambda d: d["routes"][0].update(place_ids=["lug-libreria"]),
            "URL de imagen http": lambda d: d["images"][0].update(source_url="http://example.org/i"),
        }
        for name, fn in cases.items():
            with self.subTest(name):
                self.assertTrue(self.schema_errors(self.mutated(fn)), f"el schema acepta: {name}")

    def test_schema_accepts_overture_fragment_shape(self):
        """Shape emitted by the #673 bridge (candidate POI) must be schema-valid."""
        data = full()
        data["places"][0].update(status="candidate", overture_gers_id="08f2a0b1c2d3e4f5",
                                 overture_release="2026-09-23.0", overture_confidence=0.83)
        for key in ("verified_at", "summary_original"):
            data["places"][0].pop(key)
        data["relationships"], data["routes"], data["images"] = [], [], []
        self.assertEqual(self.schema_errors(data), [])

    def test_mutation_proof_assertions_have_teeth(self):
        """Weakening the schema must make a rejected case pass, proving the assertion bites."""
        weak = copy.deepcopy(SCHEMA)
        del weak["$defs"]["place"]["unevaluatedProperties"]
        data = self.mutated(lambda d: d["places"][0].update(lattitude=1))
        self.assertTrue(self.schema_errors(data))
        self.assertEqual([e.message for e in Draft202012Validator(weak).iter_errors(data)], [])


class GateRegressionTest(unittest.TestCase):
    def issues(self, fn):
        data = full()
        fn(data)
        return mod.problems(data)

    def assertFlags(self, fn, fragment):
        issues = self.issues(fn)
        self.assertTrue(any(fragment in x for x in issues), f"{fragment!r} no está en {issues}")

    def test_baseline_clean(self):
        self.assertEqual(mod.problems(full()), [])

    def test_boolean_schema_version_rejected(self):
        self.assertEqual(mod.problems({**full(), "schema_version": True}), ["schema_version debe ser 1"])

    def test_non_dict_snapshot_does_not_crash(self):
        for value in (None, [], "x", 1):
            self.assertEqual(mod.problems(value), ["schema_version debe ser 1"])

    def test_impossible_calendar_dates(self):
        self.assertFlags(lambda d: d["places"][0].update(verified_at="2026-02-30"), "verified_at no es una fecha real")
        self.assertFlags(lambda d: d["relationships"][0].update(verified_at="2026-13-01"), "exige fecha")
        self.assertFlags(lambda d: d["sources"][0].update(retrieved_at="2026-00-10"), "retrieved_at")

    def test_non_string_date_does_not_crash(self):
        self.assertFlags(lambda d: d["places"][0].update(verified_at=20261021), "verified_at no es una fecha real")

    def test_whitespace_only_evidence_is_not_evidence(self):
        self.assertFlags(lambda d: d["relationships"][0].update(evidence_note="   "), "exige fecha")
        self.assertFlags(lambda d: d["places"][0].update(summary_original=" \n"), "texto original")
        self.assertFlags(lambda d: d["sources"][0].update(evidence_summary="  "), "requiere URL, título")

    def test_duplicate_public_slugs(self):
        self.assertFlags(lambda d: d["places"][1].update(slug="libreria"), "slug duplicado")
        self.assertFlags(lambda d: d["destinations"][1].update(slug="lisboa"), "slug duplicado")
        self.assertFlags(lambda d: d["routes"].append({**d["routes"][0], "id": "rou-b"}), "slug duplicado")

    def test_point_requires_coordinates(self):
        self.assertFlags(drop_coordinates, "point/building requiere coordenadas")

    def test_unlocated_with_only_longitude(self):
        self.assertFlags(lambda d: d["places"][1].update(geo_precision="unlocated", longitude=3), "unlocated")

    def test_osm_type_without_id(self):
        self.assertFlags(lambda d: d["places"][0].update(osm_type="node"), "osm_id y osm_type")

    def test_route_stop_from_other_destination(self):
        self.assertFlags(lambda d: d["routes"][0].update(place_ids=["lug-libreria", "lug-oporto"]),
                         "pertenece a otro destino")

    def test_place_image_ids_must_belong_to_place(self):
        self.assertFlags(lambda d: d["places"][1].update(image_ids=["img-a"]), "pertenece a otro lugar")

    def test_approved_work_needs_approved_authors(self):
        self.assertFlags(lambda d: d["authors"][0].update(status="candidate"), "authors='aut-a' no aprobado")

    def test_approved_adaptation_needs_approved_original_work(self):
        def f(d):
            d["works"][0]["status"] = "reviewed"
            d["relationships"] = []  # el único camino a la obra es la adaptación
        self.assertFlags(f, "adaptations/ada-a: works='obr-a' no aprobado")

    def test_candidate_chain_is_fine(self):
        def f(d):
            d["authors"][0]["status"] = "candidate"
            d["works"][0]["status"] = "candidate"
            d["adaptations"][0]["status"] = "candidate"
            d["relationships"][0]["status"] = "candidate"
        self.assertEqual(self.issues(f), [])

    def test_parent_destination_dangling_or_self(self):
        self.assertFlags(lambda d: d["destinations"][1].update(parent_id="dst-nope"), "destinations='dst-nope'")
        self.assertFlags(lambda d: d["destinations"][1].update(parent_id="dst-porto"), "propio destino")

    def test_approved_image_urls_are_strictly_https(self):
        self.assertFlags(lambda d: d["images"][0].update(source_url="javascript:alert(1)"), "URLs HTTPS válidas")
        self.assertFlags(lambda d: d["images"][0].update(license_url="https://u:p@example.org/l"), "URLs HTTPS válidas")

    def test_candidate_image_with_bad_url_is_not_gated(self):
        self.assertEqual(self.issues(lambda d: d["images"][0].update(status="candidate", source_url="x")), [])

    def test_nan_and_infinity_coordinates(self):
        for bad in (float("nan"), float("inf")):
            self.assertFlags(lambda d, b=bad: d["places"][0].update(latitude=b), "latitude fuera de rango")

    def test_duplicate_ids_within_collection(self):
        self.assertFlags(lambda d: d["authors"].append(copy.deepcopy(d["authors"][0])), "id duplicado")

    def test_non_object_entries_do_not_crash(self):
        self.assertFlags(lambda d: d["places"].append("x"), "objeto esperado")


class CliTest(unittest.TestCase):
    def run_cli(self, path):
        return subprocess.run([sys.executable, str(ROOT / "scripts/atlas_contract_check.py"), str(path)],
                              capture_output=True, text=True)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            good, bad, broken = Path(tmp, "g.json"), Path(tmp, "b.json"), Path(tmp, "x.json")
            good.write_text(json.dumps(full()), encoding="utf-8")
            data = full()
            data["places"][0]["slug"] = "biblioteca"
            bad.write_text(json.dumps(data), encoding="utf-8")
            broken.write_text("{no json", encoding="utf-8")
            self.assertEqual(self.run_cli(good).returncode, 0)
            self.assertEqual(self.run_cli(bad).returncode, 1)
            self.assertEqual(self.run_cli(broken).returncode, 2)
            self.assertEqual(self.run_cli(Path(tmp, "missing.json")).returncode, 2)


if __name__ == "__main__":
    unittest.main()
