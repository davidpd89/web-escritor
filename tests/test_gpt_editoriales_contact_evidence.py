"""Offline contracts for publisher evidence, extraction and the real builder."""
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

    def test_same_fact_with_another_id_is_not_extra_evidence(self):
        r = run(observation(), observation("sol-copy"))
        self.assertEqual(len(r["publishers"][0]["submission_status_candidates"]), 1)
        self.assertEqual(r["rejected_observations"][0]["reason"], "duplicate_evidence")

    def test_dates_require_explicit_calendar_format(self):
        for checked in ("20261022", "2026-W43-4", "2026-10-32"):
            with self.subTest(checked=checked):
                r = run(observation(checked=checked))
                self.assertEqual(r["rejected_observations"][0]["reason"], "invalid_date")

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

    def test_five_short_anchors_from_official_pages_2026_10_22(self):
        # These are short excerpts from the named official pages, verified
        # against their rendered text on 2026-10-22. Not complete live HTML.
        anchors = [
            ("editorial-anagrama",
             "Editorial Anagrama mantendrá pausada temporalmente la recepción de manuscritos.",
             "paused"),
            ("nocturna-ediciones",
             "Si desea enviarnos un manuscrito, puede hacerlo vía correo electrónico a la siguiente dirección:",
             "open"),
            ("minotauro",
             "El proyecto deberá enviarse por correo electrónico a la dirección proyectosminotauro@planeta.es",
             "open"),
            ("alienta-editorial",
             "Alienta Editorial acepta la recepción de manuscritos originales.",
             "open"),
            ("alfaguara",
             "Penguin Random House Grupo Editorial solo recibe manuscritos espontáneos a través de la web.",
             "group_only"),
        ]
        for slug, phrase, expected in anchors:
            with self.subTest(slug=slug):
                from html import escape
                got = self.check_pilot(slug, "<main><p>" + escape(phrase) + "</p></main>")
                self.assertEqual(got["suggestion"], expected)
                self.assertNotIn("@", got["matching_fragment"])
                self.assertTrue(got["manual_review_required"])
                self.assertFalse(got["publish"])

    def test_contradictory_acceptance_within_same_sentence_is_unknown(self):
        negatives = [
            ("nocturna-ediciones",
             "Si desea enviarnos un manuscrito, NO lo haga por correo electrónico: la recepción de originales está cerrada."),
            ("minotauro",
             "El proyecto deberá enviarse por correo electrónico cuando reabra el plazo. Actualmente no aceptamos manuscritos."),
        ]
        for slug, phrase in negatives:
            with self.subTest(slug=slug):
                result = self.check_pilot(slug, "<main><p>" + phrase + "</p></main>")
                self.assertEqual(result["suggestion"], "unknown")
                self.assertIn("Conflicting", result["reason"])
                self.assertFalse(result["publish"])

    def test_specific_genre_or_physical_limits_do_not_force_unknown(self):
        cases = [
            ("nocturna-ediciones",
             "Si desea enviarnos un manuscrito, puede hacerlo vía correo electrónico. No recibimos manuscritos físicos."),
            ("alienta-editorial",
             "Alienta Editorial acepta la recepción de manuscritos originales. El manuscrito deberá ser un ensayo: no publicamos ficción."),
        ]
        for slug, phrase in cases:
            with self.subTest(slug=slug):
                result = self.check_pilot(slug, "<main><p>" + phrase + "</p></main>")
                self.assertEqual(result["suggestion"], "open")
                self.assertFalse(result["publish"])

    def test_manuscript_mailboxes_extracted_but_not_press_or_reader_addresses(self):
        # Sections transcribed from official pages 2026-10-22. HTML fragments
        # are reconstructed; this is NOT downloaded original HTML.
        pages = {
            "nocturna-ediciones": (
                "<h3>Prensa</h3><p>Escríbanos a info@nocturnaediciones.com.</p>"
                "<h3>Envío de manuscritos</h3><p>Si desea enviarnos un manuscrito, "
                "puede hacerlo vía correo electrónico a la siguiente dirección: "
                "manuscritos@nocturnaediciones.com.</p>"),
            "minotauro": (
                "<p>El proyecto deberá enviarse por correo electrónico a la dirección "
                "proyectosminotauro@planeta.es en formato pdf o word.</p>"
                "<p>Contacto información al lector: infominotauro@planeta.es. "
                "Prensa: prensaminotauro@planeta.es.</p>"),
            "alienta-editorial": (
                "<p>Alienta Editorial acepta la recepción de manuscritos originales.</p>"
                "<p>La dirección de correo electrónico para los manuscritos en formato "
                "digital es: alienta@planeta.es</p>"
                "<p>Contacto prensa: mjbertran@planeta.es</p>"),
        }
        expected = {
            "nocturna-ediciones": "manuscritos@nocturnaediciones.com",
            "minotauro": "proyectosminotauro@planeta.es",
            "alienta-editorial": "alienta@planeta.es",
        }
        for slug, page in pages.items():
            with self.subTest(slug=slug):
                output = self.check_pilot(slug, page)
                self.assertEqual(output["suggestion"], "open")
                self.assertEqual(output["submission_email_candidate"], expected[slug])
                self.assertEqual(output["submission_email_basis"], "explicit_manuscript_instruction")
                self.assertNotIn("@", output["matching_fragment"])
                self.assertFalse(output["publish"])

    def test_press_email_without_explicit_submission_instruction_is_not_copied(self):
        for slug, phrase in [
            ("nocturna-ediciones", "Prensa: info@nocturnaediciones.com"),
            ("minotauro", "Premio Minotauro: premiominotauro@planeta.es"),
            ("alienta-editorial", "Prensa: mjbertran@planeta.es"),
        ]:
            with self.subTest(slug=slug):
                output = self.check_pilot(slug, "<p>" + phrase + "</p>")
                self.assertEqual(output["suggestion"], "unknown")
                self.assertIsNone(output["submission_email_candidate"])

    def test_valid_status_without_explicit_email_remains_email_unknown(self):
        got = self.check_pilot(
            "alienta-editorial",
            "<p>Alienta Editorial acepta la recepción de manuscritos originales.</p>")
        self.assertEqual(got["suggestion"], "open")
        self.assertIsNone(got["submission_email_candidate"])

    def test_approval_cannot_be_inferred_from_group_or_closed_sources(self):
        for slug, html in [
            ("alfaguara", "<p>El grupo solo recibe manuscritos espontáneos a través de la web: contacto@ejemplo.com.</p>"),
            ("editorial-anagrama", "<p>Anagrama mantendrá pausada temporalmente la recepción de manuscritos. prensa@anagrama-ed.es.</p>"),
        ]:
            with self.subTest(slug=slug):
                got = self.check_pilot(slug, html)
                self.assertIsNone(got["submission_email_candidate"])
                self.assertFalse(got["publish"])

    def test_wrong_mailbox_domain_is_not_a_contact_candidate(self):
        for slug, text in [
            ("nocturna-ediciones", "Si desea enviarnos un manuscrito, puede hacerlo vía correo electrónico a la siguiente dirección: fraude@otro.com."),
            ("alienta-editorial", "Alienta Editorial acepta la recepción de manuscritos originales. La dirección de correo electrónico para los manuscritos en formato digital es: fraude@otro.com."),
        ]:
            with self.subTest(slug=slug):
                got = self.check_pilot(slug, "<p>" + text + "</p>")
                self.assertIsNone(got["submission_email_candidate"])

    def test_full_closure_wordings_are_unknown_not_open(self):
        prefix = ("Si desea enviarnos un manuscrito, puede hacerlo vía correo "
                  "electrónico a la siguiente dirección: "
                  "manuscritos@nocturnaediciones.com. ")
        for clause in [
            "No recibimos originales actualmente.",
            "Ya no estamos aceptando manuscritos.",
            "No estamos recibiendo manuscritos.",
            "Actualmente no aceptamos manuscritos.",
        ]:
            with self.subTest(clause=clause):
                outcome = self.check_pilot("nocturna-ediciones",
                                           "<p>" + prefix + clause + "</p>")
                self.assertEqual(outcome["suggestion"], "unknown")
                self.assertIsNone(outcome["submission_email_candidate"])
                self.assertFalse(outcome["publish"])

    def test_format_or_genre_restrictions_do_not_masquerade_as_closure(self):
        prefix = ("Si desea enviarnos un manuscrito, puede hacerlo vía correo "
                  "electrónico a la siguiente dirección: "
                  "manuscritos@nocturnaediciones.com. ")
        for clause in [
            "No recibimos originales en papel.",
            "No aceptamos manuscritos de ficción.",
            "No recibimos manuscritos físicos.",
        ]:
            with self.subTest(clause=clause):
                outcome = self.check_pilot("nocturna-ediciones",
                                           "<p>" + prefix + clause + "</p>")
                self.assertEqual(outcome["suggestion"], "open")
                self.assertEqual(outcome["submission_email_candidate"],
                                 "manuscritos@nocturnaediciones.com")
                self.assertFalse(outcome["publish"])

    def test_inert_template_or_head_cannot_prove_manuscript_acceptance(self):
        # HTML <template> stores unrendered markup and <head> contains
        # metadata. Neither can establish a visible submission instruction.
        phrase = "Alienta Editorial acepta la recepción de manuscritos originales."
        for wrapper in (
            "<template><p>" + phrase + "</p></template><main>Contacto general.</main>",
            "<head><title>" + phrase + "</title></head><main>Contacto general.</main>",
        ):
            with self.subTest(wrapper=wrapper[:20]):
                got = self.check_pilot("alienta-editorial", wrapper)
                self.assertEqual(got["suggestion"], "unknown")
                self.assertFalse(got["detected"])
                self.assertIsNone(got["submission_email_candidate"])

    def test_visible_body_still_proves_submission_when_template_is_present(self):
        phrase = "Alienta Editorial acepta la recepción de manuscritos originales."
        html = (
            "<head><title>Contacto</title></head>"
            "<template><p>" + phrase + "</p></template>"
            "<main><p>" + phrase + "</p></main>"
        )
        got = self.check_pilot("alienta-editorial", html)
        self.assertEqual(got["suggestion"], "open")
        self.assertTrue(got["detected"])
        self.assertFalse(got["publish"])

    def test_hidden_html_blocks_cannot_open_manuscript_intake(self):
        # These three false positives were reproduced on the local parser
        # before the fix (all incorrectly returned "open").
        phrase = "Alienta Editorial acepta la recepción de manuscritos originales."
        invisible = [
            "<main><section hidden><p>" + phrase + "</p></section><p>Contacto general</p></main>",
            "<main><section aria-hidden='true'><p>" + phrase + "</p></section><p>Contacto general</p></main>",
            "<main><section style='display:none'><p>" + phrase + "</p></section><p>Contacto general</p></main>",
            "<main><section style='visibility: hidden'><p>" + phrase + "</p></section><p>Contacto general</p></main>",
        ]
        for html in invisible:
            with self.subTest(case=html[:75]):
                result = self.check_pilot("alienta-editorial", html)
                self.assertEqual(result["suggestion"], "unknown")
                self.assertIsNone(result["submission_email_candidate"])
                self.assertFalse(result["publish"])

    def test_visible_text_after_hidden_and_void_elements_is_still_read(self):
        phrase = "Alienta Editorial acepta la recepción de manuscritos originales."
        cases = [
            "<main><section hidden><p>Prohibido enviar</p></section><p>" + phrase + "</p></main>",
            "<main><img src='/cover'><br><p>" + phrase + "</p></main>",
            "<main><section><p>" + phrase + "</p></section></main>",
        ]
        for html in cases:
            with self.subTest(case=html[:75]):
                result = self.check_pilot("alienta-editorial", html)
                self.assertEqual(result["suggestion"], "open")
                self.assertFalse(result["publish"])

    def test_far_away_general_closure_overrides_earlier_email_instruction(self):
        # A long page can show obsolete submission instructions near the top
        # and an explicit general closure several paragraphs later.
        lead = (
            "Si desea enviarnos un manuscrito, puede hacerlo vía correo "
            "electrónico a la siguiente dirección: "
            "manuscritos@nocturnaediciones.com."
        )
        long_gap = "Esta sección recoge el catálogo editorial y otras noticias. " * 12
        for end in (
            "Actualmente no aceptamos manuscritos.",
            "Ya no estamos recibiendo originales.",
        ):
            with self.subTest(closure=end):
                html = "<p>" + lead + "</p><p>" + long_gap + "</p><p>" + end + "</p>"
                output = self.check_pilot("nocturna-ediciones", html)
                self.assertEqual(output["suggestion"], "unknown")
                self.assertIsNone(output["submission_email_candidate"])
                self.assertFalse(output["publish"])

    def test_far_away_genre_or_format_limit_does_not_close_general_intake(self):
        lead = (
            "Si desea enviarnos un manuscrito, puede hacerlo vía correo "
            "electrónico a la siguiente dirección: "
            "manuscritos@nocturnaediciones.com."
        )
        long_gap = "Esta sección recoge el catálogo editorial y otras noticias. " * 12
        for end in (
            "No aceptamos manuscritos de ficción.",
            "No recibimos originales en papel.",
        ):
            with self.subTest(restriction=end):
                html = "<p>" + lead + "</p><p>" + long_gap + "</p><p>" + end + "</p>"
                output = self.check_pilot("nocturna-ediciones", html)
                self.assertEqual(output["suggestion"], "open")
                self.assertEqual(output["submission_email_candidate"],
                                 "manuscritos@nocturnaediciones.com")
                self.assertFalse(output["publish"])

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



class ExistingCachedHTTPBridgeTests(unittest.TestCase):
    """The runner and reporting bridge are tested OFFLINE with a fake get().
    The real CachedHTTP client is provided by main only at opt-in runtime.
    """
    CASES = {
        "schema_version": 1, "checked_on": "2026-10-22",
        "cases": [{"slug": slug, "official_url": url}
                  for slug, url in RealSourceSnippetPilotTests.URLS.items()],
    }
    HOSTS = {
        "schema_version": 1, "publishers": {
            slug: {"hosts": [url.split("/")[2]]}
            for slug, url in RealSourceSnippetPilotTests.URLS.items()
        },
    }

    class FakeHTTP:
        def __init__(self, pages, broken=None):
            self.pages, self.broken = pages, broken
            self.requests = 0
            self.hits = 0

        def get(self, url, *, ttl, limit):
            self.requests += 1
            if url == self.broken:
                raise ValueError("Simulated source interruption")
            return self.pages[url].encode("utf-8")

    def test_five_pages_are_read_once_and_review_only(self):
        url_by_slug = RealSourceSnippetPilotTests.URLS
        fragments = {
            "editorial-anagrama": "<p>Anagrama mantendrá pausada temporalmente la recepción de manuscritos.</p>",
            "nocturna-ediciones": "<p>Si desea enviarnos un manuscrito, puede hacerlo vía correo electrónico.</p>",
            "minotauro": "<p>El proyecto deberá enviarse por correo electrónico.</p>",
            "alienta-editorial": "<p>Alienta Editorial acepta la recepción de manuscritos originales.</p>",
            "alfaguara": "<p>El grupo solo recibe manuscritos espontáneos a través de la web.</p>",
        }
        fake = self.FakeHTTP({url: fragments[slug]
                              for slug, url in url_by_slug.items()})
        got = mod.run_live_pilot(self.CASES, self.HOSTS, as_of=TODAY,
                                 cache_dir=Path(".ci/unused"), budget=12, http=fake)
        self.assertEqual(got["requests_physical"], 5)
        self.assertEqual(len(got["results"]), 5)
        self.assertEqual({r["publisher_slug"]: r["suggestion"] for r in got["results"]},
                         {"editorial-anagrama": "paused", "nocturna-ediciones": "open",
                          "minotauro": "open", "alienta-editorial": "open",
                          "alfaguara": "group_only"})
        self.assertFalse(got["published"])
        self.assertFalse(got["writes_to_public_data"])

    def test_pilot_reports_comparison_to_prior_human_review(self):
        pages = {url: "<p>Contacto general</p>"
                 for url in RealSourceSnippetPilotTests.URLS.values()}
        cases = json.loads(json.dumps(self.CASES))
        for item in cases["cases"]:
            item["expected_pilot_candidate"] = "open"
        first = cases["cases"][0]
        pages[first["official_url"]] = (
            "<p>Anagrama mantendrá pausada temporalmente "
            "la recepción de manuscritos.</p>")
        first["expected_pilot_candidate"] = "paused"
        fake = self.FakeHTTP(pages)
        output = mod.run_live_pilot(
            cases, self.HOSTS, as_of=TODAY,
            cache_dir=Path(".ci/unused"), http=fake)
        self.assertEqual(output["compared_to_prior_review"], 5)
        self.assertEqual(output["matched_prior_review"], 1)
        self.assertEqual(output["differences_needing_human_review"], 4)
        self.assertEqual(output["retrieval_failures"], 0)
        self.assertFalse(output["published"])

    def test_failed_page_is_not_counted_as_disagreement(self):
        urls = RealSourceSnippetPilotTests.URLS
        cases = json.loads(json.dumps(self.CASES))
        for item in cases["cases"]:
            item["expected_pilot_candidate"] = "open"
        fake = self.FakeHTTP(
            {url: "<p>Contacto general</p>" for url in urls.values()},
            broken=urls["minotauro"])
        output = mod.run_live_pilot(
            cases, self.HOSTS, as_of=TODAY,
            cache_dir=Path(".ci/unused"), http=fake)
        self.assertEqual(output["compared_to_prior_review"], 4)
        self.assertEqual(output["differences_needing_human_review"], 4)
        self.assertEqual(output["retrieval_failures"], 1)
        self.assertFalse(output["published"])

    def test_source_hash_and_retrieval_metrics_are_reported(self):
        import hashlib
        urls = RealSourceSnippetPilotTests.URLS
        pages = {url: "<p>Contacto general</p>" for url in urls.values()}
        fake = self.FakeHTTP(pages)
        result = mod.run_live_pilot(self.CASES, self.HOSTS, as_of=TODAY,
                                    cache_dir=Path(".ci/unused"), http=fake)
        self.assertEqual(result["requests_physical"], 5)
        sample = result["results"][0]
        raw = pages[sample["source_url"]].encode("utf-8")
        self.assertEqual(sample["content_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(sample["content_bytes"], len(raw))
        # FakeHTTP has no actual response cache; page provenance is unknown.
        self.assertIsNone(sample["served_from_cache"])
        self.assertFalse(sample["publish"])

    def test_fake_cache_hit_is_not_confused_with_new_download(self):
        class CacheFake(self.FakeHTTP):
            def get(self, url, *, ttl, limit):
                content = super().get(url, ttl=ttl, limit=limit)
                self.hits += 1
                return content
        pages = {url: "<p>Contacto general</p>"
                 for url in RealSourceSnippetPilotTests.URLS.values()}
        out = mod.run_live_pilot(self.CASES, self.HOSTS, as_of=TODAY,
                                 cache_dir=Path(".ci/unused"), http=CacheFake(pages))
        self.assertEqual(out["cache_hits"], 5)
        # A hit counter alone is insufficient: it might only count robots.txt.
        self.assertTrue(all(r["served_from_cache"] is None for r in out["results"]))
        self.assertFalse(out["published"])

    def test_cached_robots_counter_does_not_imply_page_cache_hit(self):
        import tempfile
        pages = {url: "<p>Contacto general</p>"
                 for url in RealSourceSnippetPilotTests.URLS.values()}
        class RobotOnlyFake(self.FakeHTTP):
            def get(self, url, *, ttl, limit):
                self.hits += 1  # pretend only robots.txt was cached
                return super().get(url, ttl=ttl, limit=limit)
        with tempfile.TemporaryDirectory() as tmp:
            fake = RobotOnlyFake(pages)
            fake.cache = Path(tmp)
            fake.now = lambda: 1792670000
            out = mod.run_live_pilot(
                self.CASES, self.HOSTS, as_of=TODAY,
                cache_dir=Path(tmp), http=fake)
            self.assertEqual(out["cache_hits"], 5)
            self.assertTrue(all(r["served_from_cache"] is False for r in out["results"]))

    def test_replays_five_pages_offline_with_real_cached_http(self):
        """Integration with the production CachedHTTP, no network at all."""
        import hashlib
        import sys
        import tempfile

        scripts = str(Path(__file__).resolve().parents[1] / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        from reading_editorial_sources import CachedHTTP

        html = {
            "editorial-anagrama":
                "<p>Editorial Anagrama mantendrá pausada temporalmente la recepción de manuscritos.</p>",
            "nocturna-ediciones":
                "<p>Si desea enviarnos un manuscrito, puede hacerlo vía correo electrónico a la siguiente dirección: manuscritos@nocturnaediciones.com.</p>",
            "minotauro":
                "<p>El proyecto deberá enviarse por correo electrónico a la dirección proyectosminotauro@planeta.es.</p>",
            "alienta-editorial":
                "<p>Alienta Editorial acepta la recepción de manuscritos originales. La dirección de correo electrónico para los manuscritos en formato digital es: alienta@planeta.es.</p>",
            "alfaguara":
                "<p>Penguin Random House Grupo Editorial solo recibe manuscritos espontáneos a través de la web.</p>",
        }
        now = 1792670000
        with tempfile.TemporaryDirectory() as dirname:
            cache = Path(dirname)
            def seed(url, content):
                name = hashlib.sha256(url.encode()).hexdigest()
                (cache / (name + ".body")).write_bytes(content.encode("utf-8"))
                (cache / (name + ".json")).write_text(
                    json.dumps({"url": url, "retrieved_at": now}),
                    encoding="utf-8")

            hosts = self.HOSTS["publishers"]
            origins = {entry["hosts"][0] for entry in hosts.values()}
            for host in origins:
                seed("https://" + host + "/robots.txt", "User-agent: *\nAllow: /\n")
            for slug, url in RealSourceSnippetPilotTests.URLS.items():
                seed(url, html[slug])

            http = CachedHTTP(cache, origins, budget=12, delay=0, now=lambda: now)
            out = mod.run_live_pilot(
                self.CASES, self.HOSTS, as_of=TODAY,
                cache_dir=cache, http=http)
            self.assertEqual(out["requests_physical"], 0)
            # The production client counts cached robots.txt alongside pages:
            # four distinct origins + five page URLs, not just five hits.
            self.assertEqual(out["cache_hits"], len(origins) + len(html))
            self.assertEqual(len(out["results"]), 5)
            self.assertTrue(all(r["retrieval"] == "ok" for r in out["results"]))
            self.assertTrue(all(r["served_from_cache"] is True for r in out["results"]))
            self.assertTrue(all(r["source_retrieved_at_unix"] == now for r in out["results"]))
            self.assertEqual(
                {r["publisher_slug"]: r["suggestion"] for r in out["results"]},
                {"editorial-anagrama": "paused",
                 "nocturna-ediciones": "open",
                 "minotauro": "open", "alienta-editorial": "open",
                 "alfaguara": "group_only"},
            )
            self.assertFalse(out["published"])

    def test_five_pilot_drafts_use_e4_schema_but_cannot_be_accepted(self):
        html = {
            "editorial-anagrama":
                "<p>Editorial Anagrama mantendrá pausada temporalmente la recepción de manuscritos.</p>",
            "nocturna-ediciones":
                "<p>Si desea enviarnos un manuscrito, puede hacerlo vía correo electrónico a la siguiente dirección: manuscritos@nocturnaediciones.com.</p>",
            "minotauro":
                "<p>El proyecto deberá enviarse por correo electrónico a la dirección proyectosminotauro@planeta.es.</p>",
            "alienta-editorial":
                "<p>Alienta Editorial acepta la recepción de manuscritos originales.</p>",
            "alfaguara":
                "<p>Penguin Random House Grupo Editorial solo recibe manuscritos espontáneos a través de la web.</p>",
        }
        pages = {RealSourceSnippetPilotTests.URLS[slug]: fragment
                 for slug, fragment in html.items()}
        result = mod.run_live_pilot(
            self.CASES, self.HOSTS, as_of=TODAY,
            cache_dir=Path(".ci/unused"), http=self.FakeHTTP(pages))
        pending = result["pending_review_observations"]
        self.assertEqual(pending["schema_version"], 1)
        self.assertEqual(len(pending["observations"]), 5)
        self.assertTrue(all(o["origin"] == "html_pilot_unreviewed"
                            for o in pending["observations"]))
        self.assertFalse(any("@" in o["evidence_summary"]
                             for o in pending["observations"]))
        # E4 must FAIL CLOSED until a person independently rechecks the page.
        staged = mod.review(pending, self.HOSTS, as_of=TODAY)
        self.assertEqual(staged["publishers"], [])
        self.assertEqual(len(staged["rejected_observations"]), 5)
        self.assertEqual({item["reason"] for item in staged["rejected_observations"]},
                         {"automated_evidence_needs_human_review"})
        self.assertFalse(staged["writes_to_public_data"])

    def test_unknown_or_failed_page_has_no_promotable_observation(self):
        urls = RealSourceSnippetPilotTests.URLS
        fake = self.FakeHTTP({url: "<p>Contacto general</p>" for url in urls.values()},
                             broken=urls["nocturna-ediciones"])
        output = mod.run_live_pilot(
            self.CASES, self.HOSTS, as_of=TODAY,
            cache_dir=Path(".ci/unused"), http=fake)
        self.assertEqual(output["pending_review_observations"]["observations"], [])
        self.assertEqual(output["retrieval_failures"], 1)
        self.assertFalse(output["published"])

    def test_failing_source_does_not_change_other_four(self):
        urls = RealSourceSnippetPilotTests.URLS
        fake = self.FakeHTTP({url: "<p>Contacto general</p>" for url in urls.values()},
                             broken=urls["minotauro"])
        got = mod.run_live_pilot(self.CASES, self.HOSTS, as_of=TODAY,
                                 cache_dir=Path(".ci/unused"), http=fake)
        self.assertEqual(got["requests_physical"], 5)
        broken, = (r for r in got["results"] if r["publisher_slug"] == "minotauro")
        self.assertEqual(broken["retrieval"], "blocked_or_failed")
        self.assertEqual(broken["suggestion"], "unknown")

    def test_modifying_exact_url_within_same_approved_host_is_rejected(self):
        cases = json.loads(json.dumps(self.CASES))
        cases["cases"][0]["official_url"] = "https://www.anagrama-ed.es/contacto"
        with self.assertRaises(ValueError):
            mod.run_live_pilot(cases, self.HOSTS, as_of=TODAY,
                               cache_dir=Path(".ci/unused"), http=self.FakeHTTP({}))

    def test_no_network_and_no_files_if_source_list_is_invalid(self):
        cases = {"schema_version": 1, "checked_on": "2026-10-22", "cases": []}
        with self.assertRaises(ValueError):
            mod.run_live_pilot(cases, self.HOSTS, as_of=TODAY,
                               cache_dir=Path(".ci/unused"), http=self.FakeHTTP({}))



class AlientaRealBuilderContractTests(unittest.TestCase):
    """Actual main build-editoriales.py validates a staged candidate in memory.

    No network, writes to a temporary file only. No generated public pages.
    """
    def test_alienta_passes_builder_but_is_not_published(self):
        import copy
        import tempfile
        import sys

        root = Path(__file__).resolve().parents[1]
        script_dir = str(root / "scripts")
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        spec = importlib.util.spec_from_file_location(
            "build_editoriales_e6_research",
            root / "scripts" / "build-editoriales.py",
        )
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)

        current = json.loads((root / "data" / "editoriales.json").read_text(encoding="utf-8"))
        candidate_doc = json.loads((root / "docs/research/gpt/editoriales-alienta-candidata-2026-10-22.json").read_text(encoding="utf-8"))
        candidate = copy.deepcopy(candidate_doc["proposed_publisher"])
        self.assertFalse(candidate["publish"])
        self.assertTrue(candidate["sources"][0]["primary"])
        self.assertNotIn(candidate["slug"], {p["slug"] for p in current["publishers"]})

        test_data = copy.deepcopy(current)
        test_data["publishers"].append(candidate)
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            data_file = temp_root / "editoriales-candidate.json"
            data_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding="utf-8")

            # The real production validator checks all 150 existing rows plus
            # the candidate; published output remains unchanged.
            _, public_rows, warnings = builder.load_and_validate(data_file, TODAY)
            self.assertEqual(len(public_rows), sum(p.get("publish") is True for p in current["publishers"]))
            self.assertNotIn("alienta-editorial", {p["slug"] for p in public_rows})
            self.assertTrue(any("alienta-editorial" in w and "publish" in w for w in warnings))
            count, build_warnings = builder.build(data_file, temp_root / "site", TODAY, True)
            self.assertEqual(count, len(public_rows))
            self.assertFalse((temp_root / "site").exists())
            self.assertEqual(warnings, build_warnings)

            # Switching publish on IN A TEMPORARY COPY validates the complete
            # record but does not write any page to the repository.
            candidate["publish"] = True
            test_data["publishers"][-1] = candidate
            data_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding="utf-8")
            count_with_alienta, _ = builder.build(data_file, temp_root / "site", TODAY, True)
            self.assertEqual(count_with_alienta, count + 1)
            self.assertFalse((temp_root / "site").exists())


if __name__ == "__main__":
    unittest.main()
