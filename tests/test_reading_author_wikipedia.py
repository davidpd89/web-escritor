"""Biografías breves desde Wikipedia: identidad estricta y sin red."""
import io
import json
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_author_wikipedia import WikipediaSummaries, clean_extract, fill_missing_bios, select_wikipedia_bio

GOOD = {'type': 'standard', 'title': 'Roald Dahl', 'description': 'escritor británico',
        'extract': 'Roald Dahl fue un novelista, cuentista, poeta y guionista británico de ascendencia noruega, célebre por sus cuentos infantiles.',
        'content_urls': {'desktop': {'page': 'https://es.wikipedia.org/wiki/Roald_Dahl'}}}


class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False


class WikipediaBioTests(unittest.TestCase):
    def test_accepts_exact_title_with_literary_occupation(self):
        found = select_wikipedia_bio('Roald Dahl', GOOD)
        self.assertEqual(found['biografia_fuente_nombre'], 'Wikipedia')
        self.assertTrue(found['biografia_fuente_url'].startswith('https://es.wikipedia.org/wiki/'))

    def test_rejects_homonym_disambiguation_other_title_or_no_occupation(self):
        for change in ({'type': 'disambiguation'}, {'title': 'Roald Dahl (futbolista)'}, {'description': 'ciudad de Francia'},
                       {'extract': 'Breve.'}, {'content_urls': {'desktop': {'page': 'https://example.com/x'}}}):
            with self.subTest(change=change):
                self.assertIsNone(select_wikipedia_bio('Roald Dahl', {**GOOD, **change}))

    def test_long_extract_is_cut_at_a_sentence(self):
        text = ('Una frase completa de ejemplo con contenido suficiente. ' * 20).strip()
        cut = clean_extract(text)
        self.assertLessEqual(len(cut), 600)
        self.assertTrue(cut.endswith('.'))

    def test_manual_and_already_filled_authors_are_not_touched_and_misses_are_not_retried_daily(self):
        authors = {'autores': [
            {'nombre': 'Manual', 'tipo': 'manual', 'nacimiento': '1960-01-01'},
            {'nombre': 'Con bio', 'tipo': 'bibliografico', 'biografia_breve': 'x' * 40},
            {'nombre': 'Roald Dahl', 'tipo': 'bibliografico'},
            {'nombre': 'Sin artículo', 'tipo': 'bibliografico'}]}
        calls = []
        def lookup(name):
            calls.append(name)
            return GOOD if name == 'Roald Dahl' else None
        self.assertEqual(fill_missing_bios(authors, lookup, '2026-10-21'), 1)
        self.assertEqual(calls, ['Roald Dahl', 'Sin artículo'])
        fill_missing_bios(authors, lookup, '2026-10-22')
        self.assertEqual(calls, ['Roald Dahl', 'Sin artículo'], 'un intento fallido espera 30 días')

    def test_client_404_is_normal_but_other_errors_stop_the_provider(self):
        def opener(code):
            def inner(request, timeout=0):
                raise HTTPError(request.full_url, code, 'x', {}, None)
            return inner
        client = WikipediaSummaries(delay=0, opener=opener(404))
        self.assertIsNone(client('Alguien'))
        self.assertFalse(client.unavailable)
        broken = WikipediaSummaries(delay=0, opener=opener(429))
        self.assertIsNone(broken('Alguien'))
        self.assertTrue(broken.unavailable)
        self.assertIsNone(broken('Otro'))
        self.assertEqual(broken.requests, 1)

    def test_budget_is_enforced(self):
        client = WikipediaSummaries(delay=0, budget=1, opener=lambda r, timeout=0: Response(json.dumps(GOOD).encode()))
        self.assertEqual(client('Roald Dahl')['title'], 'Roald Dahl')
        self.assertIsNone(client('Roald Dahl'))


if __name__ == '__main__':
    unittest.main()
