"""Synthetic, NOT EXECUTED regression fixtures for Wikidata CC0 publisher staging."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/gpt_editoriales_wikidata_candidates.py"
spec = importlib.util.spec_from_file_location("gpt_editoriales_wikidata_candidates", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def statement(value, rank="normal", snaktype="value"):
    return {"rank": rank, "mainsnak": {"snaktype": snaktype, "datavalue": {"value": value}}}


def entity(qid="Q123", label="Editorial Ejemplo", website="https://editorial-ejemplo.es",
           parent="Q11", cls="Q22", country="Q29", deprecated=None):
    claims = {
        "P856": [statement(website)] if website is not None else [],
        "P749": [statement({"id": parent})] if parent else [],
        "P31": [statement({"id": cls})] if cls else [],
        "P17": [statement({"id": country})] if country else [],
    }
    if deprecated is not None:
        claims["P856"].append(statement(deprecated, rank="deprecated"))
    return {"id": qid, "labels": {"es": {"language": "es", "value": label}},
            "aliases": {"es": [{"language": "es", "value": "Ejemplo Libros"}]},
            "claims": claims}


class WikidataCandidateTests(unittest.TestCase):
    def test_valid_snapshot_yields_review_only_not_contact(self):
        data = module.candidates({"entities": {"Q123": entity()}},
                                 {"publishers": [{"slug": "editorial-ejemplo",
                                                  "name": "Editorial Ejemplo",
                                                  "website_url": "https://editorial-ejemplo.es/contacto"}]})
        found, = data["candidates"]
        self.assertEqual(found["possible_existing_slugs"], ["editorial-ejemplo"])
        self.assertEqual(found["parent_qids"], ["Q11"])
        self.assertEqual(found["class_qids"], ["Q22"])
        self.assertEqual(found["country_qids"], ["Q29"])
        self.assertEqual(found["website_candidates"], ["https://editorial-ejemplo.es"])
        self.assertTrue(found["manual_review_required"])
        self.assertFalse(found["contact_publication_authorized"])
        self.assertEqual(found["manuscript_status"], "not_inferred")

    def test_no_sources_does_not_generate_website(self):
        snapshot = {"entities": {"Q123": entity(website=None, label="Otra Editorial")}}
        data = module.candidates(snapshot, {"publishers": []})
        self.assertEqual(data["candidates"][0]["website_candidates"], [])

    def test_deprecated_website_not_selected(self):
        snapshot = {"entities": {"Q123": entity(deprecated="https://antigua-editorial.es")}}
        found = module.candidates(snapshot, {"publishers": []})["candidates"][0]
        self.assertNotIn("https://antigua-editorial.es", found["website_candidates"])

    def test_preferred_rank_takes_precedence(self):
        x = entity()
        x["claims"]["P856"].extend([statement("https://preferida.es", rank="preferred")])
        data = module.candidates({"entities": {"Q123": x}}, {"publishers": []})
        self.assertEqual(data["candidates"][0]["website_candidates"], ["https://preferida.es"])

    def test_rejects_suspicious_domains_and_private_hosts(self):
        for url in ("http://editorial-ejemplo.es", "https://127.0.0.1",
                    "https://localhost", "https://publisher.local",
                    "https://example.invalid", "https://user@editorial-ejemplo.es",
                    "https://editorial-ejemplo.es:8080", "https://editorial-ejemplo.es/#f",
                    "https://editorial-ejemplo.es.evil.example", "javascript:alert(1)"):
            with self.subTest(url=url):
                self.assertIsNone(module.safe_website(url))

    def test_missing_or_mismatched_qid_is_rejected(self):
        x = module.candidates({"entities": {"Q123": entity("Q124"), "Qxx": entity("Qxx")}},
                              {"publishers": []})
        self.assertEqual(x["candidates"], [])
        self.assertEqual(x["rejected_ids"], ["Q123", "Qxx"])

    def test_unknown_identity_cannot_infer_company_or_manuscript_status(self):
        data = module.candidates({"entities": {"Q123": entity(
            label="La persona de nombre Editorial",
            website="https://persona-ejemplo.es", cls="Q5")}}, {"publishers": []})
        found = data["candidates"][0]
        self.assertEqual(found["class_qids"], ["Q5"])
        self.assertTrue(found["manual_review_required"])
        self.assertEqual(found["manuscript_status"], "not_inferred")

    def test_ambiguous_shared_group_domain_keeps_both_matches(self):
        sample = {"entities": {"Q123": entity(label="Sello Desconocido", website="https://grupo-editorial.es")}}
        local = {"publishers": [
            {"slug": "sello-a", "name": "Sello A", "website_url": "https://grupo-editorial.es/a"},
            {"slug": "sello-b", "name": "Sello B", "website_url": "https://grupo-editorial.es/b"},
        ]}
        found = module.candidates(sample, local)["candidates"][0]
        self.assertEqual(found["possible_existing_slugs"], ["sello-a", "sello-b"])

    def test_unknown_entity_or_directory_format_fails_closed(self):
        for entities, directory in [({}, {}), ([], {"publishers": []}),
                                    ({"Q123": entity()}, {"publishers": ["invalid"]})]:
            with self.subTest(entities=entities):
                with self.assertRaises(ValueError):
                    module.candidates({"entities": entities}, directory)


if __name__ == "__main__":
    unittest.main()
