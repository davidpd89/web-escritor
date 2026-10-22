"""Synthetic contracts for publisher proof staging. Prepared only; NOT executed."""
import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/gpt_editoriales_contact_evidence.py"
spec = importlib.util.spec_from_file_location("gpt_editoriales_contact_evidence", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
TODAY = date(2026, 10, 22)
HOSTS = {"schema_version": 1, "publishers": {
    "editorial-sol": {"hosts": ["editorial-sol.es", "grupo-oficial.es"]},
    "editorial-luna": {"hosts": ["grupo-oficial.es"]}}}


def observation(ident="sol-1", slug="editorial-sol", purpose="submissions_open",
                scope="publisher_specific", url="https://editorial-sol.es/manuscritos",
                checked="2026-10-21", summary="La editorial publica de modo expreso el canal de envío."):
    return {"id": ident, "publisher_slug": slug, "purpose": purpose, "scope": scope,
            "source_url": url, "checked_at": checked, "evidence_summary": summary}


def run(*items, hosts=HOSTS, as_of=TODAY):
    return mod.review({"schema_version": 1, "observations": list(items)}, hosts, as_of=as_of)


class ContactEvidenceTests(unittest.TestCase):
    def test_specific_open_status_is_candidate_only(self):
        r = run(observation())
        pub, = r["publishers"]
        self.assertEqual(pub["proposed_manuscript_status"], "open")
        self.assertTrue(pub["manual_review_required"])
        self.assertFalse(pub["publication_allowed"])
        self.assertFalse(r["writes_to_public_data"])

    def test_paused_is_closed_when_official_and_fresh(self):
        r = run(observation(purpose="submissions_paused"))
        self.assertEqual(r["publishers"][0]["proposed_manuscript_status"], "closed")

    def test_general_contact_never_implies_submission(self):
        r = run(observation(purpose="general_contact"))
        self.assertEqual(r["publishers"][0]["proposed_manuscript_status"], "not_inferred")
        self.assertEqual(len(r["publishers"][0]["general_sources"]), 1)

    def test_press_contact_is_separate(self):
        r = run(observation(purpose="press_contact"))
        self.assertEqual(len(r["publishers"][0]["press_sources"]), 1)
        self.assertEqual(len(r["publishers"][0]["general_sources"]), 0)

    def test_group_policy_never_inherited_by_siblings(self):
        r = run(observation(purpose="group_submission_channel", scope="group_general",
                            slug="editorial-luna", url="https://grupo-oficial.es/envios"))
        pub, = r["publishers"]
        self.assertEqual(pub["proposed_manuscript_status"], "not_inferred")
        self.assertEqual(len(pub["group_submission_sources"]), 1)

    def test_group_general_submissions_open_never_inherits(self):
        r = run(observation(purpose="submissions_open", scope="group_general",
                            slug="editorial-luna", url="https://grupo-oficial.es/envios"))
        self.assertEqual(r["publishers"][0]["submission_status_candidates"][0]["proposed_status"], "unknown")

    def test_stale_status_requires_new_review_not_closed(self):
        r = run(observation(checked="2026-07-01"))
        entry, = r["publishers"][0]["submission_status_candidates"]
        self.assertTrue(entry["expired"])
        self.assertEqual(r["publishers"][0]["proposed_manuscript_status"], "not_inferred")

    def test_conflicting_sources_do_not_select_winner(self):
        r = run(observation(), observation("sol-2", purpose="submissions_paused",
                                          url="https://editorial-sol.es/cerrado"))
        self.assertEqual(r["publishers"][0]["proposed_manuscript_status"], "conflict_review")

    def test_off_host_or_subdomain_is_quarantined(self):
        for url in ["https://editorial-sol.es.malicioso.es/envios",
                    "http://editorial-sol.es/envios", "https://editorial-sol.es:8080/",
                    "https://127.0.0.1", "https://otro.es/"]:
            with self.subTest(url=url):
                r = run(observation(url=url))
                self.assertEqual(len(r["publishers"]), 0)
                self.assertEqual(r["rejected_observations"][0]["reason"], "source_host_not_approved")

    def test_duplicate_ids_rejected(self):
        r = run(observation(), observation(purpose="press_contact"))
        self.assertEqual(len(r["rejected_observations"]), 1)
        self.assertEqual(r["rejected_observations"][0]["reason"], "missing_or_duplicate_id")

    def test_future_date_is_rejected(self):
        r = run(observation(checked="2027-01-01"))
        self.assertEqual(r["rejected_observations"][0]["reason"], "future_evidence")

    def test_fake_email_not_added_to_reports(self):
        r = run(observation(summary="Escribir directamente a pruebas@editorial-sol.es"))
        self.assertEqual(r["rejected_observations"][0]["reason"], "possible_personal_data_or_address")
        self.assertNotIn("pruebas@editorial-sol.es", json.dumps(r))

    def test_approved_host_requires_independent_vetting(self):
        with self.assertRaises(ValueError):
            run(observation(), hosts={"schema_version": 1, "publishers": {
                "editorial-sol": {"hosts": ["https://editorial-sol.es"]}}})

    def test_catalogue_imprint_does_not_infer_submissions(self):
        r = run(observation(purpose="publisher_imprint", url="https://grupo-oficial.es/sellos"))
        pub, = r["publishers"]
        self.assertEqual(pub["proposed_manuscript_status"], "not_inferred")
        self.assertEqual(len(pub["publisher_sources"]), 1)

    def test_unknown_publisher_is_quarantined(self):
        r = run(observation(slug="otra-editorial"))
        self.assertEqual(r["rejected_observations"][0]["reason"], "publisher_not_approved")



class RealSourceSnippetPilotTests(unittest.TestCase):
    """Manually selected fragments based on 22/10/2026 official pages.
    NOT the live pages' HTML; real HTTP/DOM regression remains untested.
    """
    URLS = {
        "editorial-anagrama": "https://www.anagrama-ed.es/manuscritos",
        "nocturna-ediciones": "https://www.nocturnaediciones.com/contacto",
        "minotauro": "https://www.planetadelibros.com/editorial/minotauro/21",
        "alienta-editorial": "https://www.planetadelibros.com/editorial/alienta-editorial/15",
        "alfaguara": "https://www.penguinrandomhousegrupoeditorial.com/sellos-y-negocios/quiero-enviar-un-manuscrito/",
    }

    def check_pilot(self, slug, html):
        return mod.draft_from_html(
            html, slug=slug, source_url=self.URLS[slug],
            checked_at="2026-10-22", source_allowlist=self.URLS,
        )

    def test_five_real_editorial_cases_as_short_html_fixtures(self):
        examples = [
            ("editorial-anagrama",
             "<main><p>Editorial Anagrama mantendrá pausada temporalmente la recepción de manuscritos.</p></main>",
             "paused", "publisher_specific"),
            ("nocturna-ediciones",
             "<h3>Envío de manuscritos</h3><p>Si desea enviarnos un manuscrito, puede hacerlo vía correo electrónico a la siguiente dirección.</p>",
             "open", "publisher_specific"),
            ("minotauro",
             "<h2>Sobre el envío de proyectos</h2><p>El proyecto deberá enviarse por correo electrónico en formato pdf o word.</p>",
             "open", "publisher_specific"),
            ("alienta-editorial",
             "<main><p>Alienta Editorial acepta la recepción de manuscritos originales.</p></main>",
             "open", "publisher_specific"),
            ("alfaguara",
             "<p>Penguin Random House Grupo Editorial solo recibe manuscritos espontáneos a través de la web.</p>",
             "group_only", "group_general"),
        ]
        for slug, snippet, decision, scope in examples:
            with self.subTest(slug=slug):
                got = self.check_pilot(slug, snippet)
                self.assertEqual(got["suggestion"], decision)
                self.assertEqual(got["scope"], scope)
                self.assertTrue(got["manual_review_required"])
                self.assertFalse(got["publish"])

    def test_absence_of_explicit_evidence_is_unknown_for_all_five(self):
        for slug in self.URLS:
            with self.subTest(slug=slug):
                got = self.check_pilot(slug, "<p>Contactar con la editorial.</p>")
                self.assertEqual(got["suggestion"], "unknown")

    def test_hidden_script_cannot_infer_status(self):
        got = self.check_pilot(
            "alienta-editorial",
            "<script>Alienta Editorial acepta la recepción de manuscritos originales.</script><p>Contacto general</p>",
        )
        self.assertEqual(got["suggestion"], "unknown")

    def test_unreviewed_or_swapped_url_is_rejected(self):
        with self.assertRaises(ValueError):
            mod.draft_from_html(
                "<p>Alienta Editorial acepta la recepción de manuscritos originales.</p>",
                slug="alienta-editorial", source_url=self.URLS["minotauro"],
                checked_at="2026-10-22", source_allowlist=self.URLS,
            )

    def test_no_emails_copied_to_experimental_fragment(self):
        got = self.check_pilot(
            "minotauro",
            "<p>El proyecto deberá enviarse por correo electrónico: ejemplos@editorial.es</p>",
        )
        self.assertEqual(got["suggestion"], "open")
        self.assertNotIn("@", got["matching_fragment"])


if __name__ == "__main__":
    unittest.main()
