"""Enlaces de terceros de las fichas de autor: solo se enlaza lo que respondió (check-links de la PR #1546)."""
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_author_links as links  # noqa: E402


class AuthorLinksTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name)
        (self.root / 'data/reading-author-texts').mkdir(parents=True)
        (self.root / 'data/reading-authors.json').write_text(json.dumps({'autores': [
            {'nombre': 'A', 'identificadores': {'web': 'https://viva.example/'}},
            {'nombre': 'B', 'identificadores': {'web': 'https://caducada.example/'}}]}), encoding='utf-8')
        (self.root / 'data/reading-author-texts/a.json').write_text(json.dumps({'fuentes': [
            {'titulo': 'Bloquea', 'url': 'https://bloquea.example/x'}]}), encoding='utf-8')
        links._cache.clear()
        self.addCleanup(links._cache.clear)

    def fetch(self, url):
        return {'https://viva.example/': 200, 'https://caducada.example/': 'error: SSLError', 'https://bloquea.example/x': 403}[url]

    def test_only_what_answered_is_linked_and_unchecked_never_is(self):
        self.assertFalse(links.alive('https://viva.example/', self.root))  # sin comprobar: no se enlaza
        links.check(self.root, today=date(2026, 11, 23), fetch=self.fetch)
        self.assertTrue(links.alive('https://viva.example/', self.root))
        self.assertFalse(links.alive('https://caducada.example/', self.root))
        self.assertFalse(links.alive('https://bloquea.example/x', self.root))

    def test_recent_results_are_reused_and_old_ones_rechecked(self):
        links.check(self.root, today=date(2026, 11, 23), fetch=self.fetch)
        calls = []
        links.check(self.root, today=date(2026, 12, 1), fetch=lambda u: calls.append(u) or 200)
        self.assertEqual(calls, [])
        links.check(self.root, today=date(2027, 1, 1), fetch=lambda u: calls.append(u) or 200)
        self.assertEqual(len(calls), 3)

    def test_the_link_check_and_this_module_agree_on_the_client(self):
        workflow = (ROOT / '.github/workflows/broken-links.yml').read_text(encoding='utf-8')
        self.assertIn(links.USER_AGENT, workflow)
        self.assertIn("--accept '200..=299,429'", workflow)

    def test_every_rendered_author_link_was_checked(self):
        # Las fichas versionadas solo enlazan webs y fuentes de autor que respondieron.
        state = json.loads((ROOT / links.STATE).read_text(encoding='utf-8'))
        for url in links.urls(ROOT):
            if not links.ok(state.get(url, {}).get('estado')):
                for page in (ROOT / 'recomendaciones/autores').glob('*/index.html'):
                    self.assertNotIn('href="' + url.replace('&', '&amp;') + '"', page.read_text(encoding='utf-8'), (url, page))


if __name__ == '__main__':
    unittest.main()
