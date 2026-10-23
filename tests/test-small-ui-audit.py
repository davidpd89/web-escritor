"""Fixtures for new advisory audits; no network or browser dependencies."""
import importlib.util
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('small_ui_audit', root/'scripts/audit-small-ui-contracts.py')
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


class SmallUiAuditTests(unittest.TestCase):
    def rules(self, html, files=()):
        return [r['rule'] for r in audit.audit_html(html, 'cuaderno/index.html', set(files))]

    def test_named_disclosure_and_nested_independent_disclosures(self):
        self.assertEqual(self.rules('<details><summary>A</summary><details><summary>B</summary></details></details>'), [])

    def test_missing_late_and_duplicate_summary(self):
        for html in ['<details>Body</details>', '<details><p>Body</p><summary>Name</summary></details>', '<details><summary>A</summary><summary>B</summary></details>']:
            with self.subTest(html=html):
                self.assertIn('details-summary', self.rules(html))

    def test_hidden_icon_does_not_name_summary(self):
        self.assertIn('summary-name', self.rules('<details><summary><span aria-hidden="true">+</span></summary></details>'))

    def test_accessible_label_and_labelledby(self):
        self.assertEqual(self.rules('<p id="n">Name</p><details><summary aria-labelledby="n"></summary></details><details><summary aria-label="Name"></summary></details>'), [])

    def test_explicitly_referenced_hidden_name_is_valid(self):
        self.assertEqual(self.rules('<span hidden id="n">Menu</span><details><summary aria-labelledby="n"></summary></details>'), [])

    def test_inert_template_does_not_report_uninstantiated_markup(self):
        self.assertEqual(self.rules('<template><details><summary></summary></details><input list="missing"></template>'), [])

    def test_option_values_are_scoped_to_each_select(self):
        self.assertEqual(self.rules('<select><option value="a">A</option></select><select><option value="a">A</option></select>'), [])

    def test_duplicate_option_across_optgroups(self):
        self.assertIn('select-value', self.rules('<select><optgroup label="A"><option value="same">A</option></optgroup><optgroup label="B"><option value="same">B</option></optgroup></select>'))

    def test_implicit_values_and_disabled_placeholders(self):
        self.assertIn('select-value', self.rules('<select><option> A </option><option>A</option></select>'))
        self.assertEqual(self.rules('<select><option value="x" disabled>Placeholder</option><option value="x">X</option></select>'), [])

    def test_omitted_option_end_tags(self):
        self.assertIn('select-value', self.rules('<select><option>A<option>A</select>'))
        self.assertEqual(self.rules('<select><option>A<option>B</select>'), [])

    def test_disabled_optgroup_does_not_create_ambiguous_choice(self):
        self.assertEqual(self.rules('<select><optgroup disabled><option value="a">A</optgroup><option value="a">A</select>'), [])

    def test_single_and_multiple_selected(self):
        options = '<option selected>A</option><option selected>B</option>'
        self.assertIn('select-selected', self.rules('<select>'+options+'</select>'))
        self.assertEqual(self.rules('<select multiple>'+options+'</select>'), [])

    def test_suggestion_list_requires_actual_datalist(self):
        self.assertIn('input-list', self.rules('<input list="d"><div id="d"></div>'))
        self.assertIn('input-list', self.rules('<input list="absent">'))
        self.assertEqual(self.rules('<input list="d"><datalist id="d"><option value="A"></datalist>'), [])

    def test_relative_encoded_download_and_case(self):
        self.assertEqual(self.rules('<a download href="../assets/gu%C3%ADa.pdf?v=1">PDF</a>', ['assets/guía.pdf']), [])
        self.assertIn('download-target', self.rules('<a download href="/Assets/book.pdf">PDF</a>', ['assets/book.pdf']))

    def test_download_directory_traversal_and_empty_href(self):
        for href in ['/assets/', '../../../secret', '']:
            with self.subTest(href=href):
                self.assertIn('download-target', self.rules(f'<a download href="{href}">Download</a>'))

    def test_external_and_generated_downloads(self):
        self.assertIn('download-origin', self.rules('<a download href="https://example.com/book.pdf">PDF</a>'))
        self.assertEqual(self.rules('<a download href="data:text/plain,hello">Text</a><a download href="blob:https://davidportodiaz.com/id">File</a>'), [])

    def test_same_origin_explicit_default_port(self):
        self.assertEqual(self.rules('<a download href="https://davidportodiaz.com:443/assets/a.pdf">PDF</a>', ['assets/a.pdf']), [])
        self.assertIn('download-origin', self.rules('<a download href="http://davidportodiaz.com/assets/a.pdf">PDF</a>', ['assets/a.pdf']))

    def test_invalid_url_is_reported_without_crashing_other_checks(self):
        self.assertIn('download-target', self.rules('<a download href="https://[broken">PDF</a>'))

    def test_impossible_numeric_bounds(self):
        self.assertIn('numeric-bounds', self.rules('<input type="number" min="10" max="2">'))
        self.assertIn('numeric-bounds', self.rules('<input type="range" min="0.2" max="0.1">'))

    def test_equal_negative_exponential_and_unbounded_numbers(self):
        self.assertEqual(self.rules('<input type="number" min="-1e2" max="-1"><input type="range" min="2" max="2"><input type="number">'), [])

    def test_invalid_numeric_step(self):
        for step in ['0', '-0.1']:
            with self.subTest(step=step):
                self.assertIn('numeric-step', self.rules(f'<input type="number" step="{step}">'))

    def test_fractional_and_unrestricted_steps(self):
        self.assertEqual(self.rules('<input type="number" step="0.01"><input type="number" step="any">'), [])

    def test_numeric_constraints_do_not_apply_to_text_input(self):
        self.assertEqual(self.rules('<input type="text" min="10" max="2">'), [])

    def test_external_form_owner_must_be_form(self):
        self.assertEqual(self.rules('<form id="f"></form><button form="f">Send</button>'), [])
        self.assertIn('form-owner', self.rules('<div id="f"></div><button form="f">Send</button>'))
        self.assertIn('form-owner', self.rules('<input form="missing">'))

    def test_coverage_counters_distinguish_unexercised_rules(self):
        counts = {}
        audit.audit_html('<input type="number"><button form="f">Send</button><form id="f"></form>', 'index.html', set(), counts)
        self.assertEqual(counts, dict(numeric_inputs=1, form_references=1))

    def test_json_duplicate_keys_are_not_silently_overwritten(self):
        self.assertTrue(audit.audit_json('{"price":1,"price":2}', 'data/books.json'))

    def test_json_nested_duplicate_keys(self):
        self.assertTrue(audit.audit_json('{"books":[{"id":1,"id":2}]}', 'data/books.json'))

    def test_json_escaped_equivalent_keys(self):
        self.assertTrue(audit.audit_json(r'{"id":1,"\u0069d":2}', 'data/books.json'))

    def test_json_separate_objects_may_share_key_names(self):
        self.assertEqual(audit.audit_json('[{"id":1},{"id":2}]', 'data/books.json'), [])

    def test_json_nonstandard_numbers(self):
        for constant in ['NaN', 'Infinity', '-Infinity']:
            with self.subTest(constant=constant):
                self.assertTrue(audit.audit_json('{"rating":'+constant+'}', 'data/books.json'))

    def test_json_strings_and_case_sensitive_keys_remain_valid(self):
        self.assertEqual(audit.audit_json('{"id":"NaN","ID":"Infinity"}', 'data/books.json'), [])

    def test_json_syntax_error_has_its_real_line(self):
        finding = audit.audit_json('{\n"id":\n}', 'data/books.json')[0]
        self.assertEqual(finding['line'], 3)


if __name__ == '__main__':
    unittest.main()
