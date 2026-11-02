"""El índice recomendaciones/llms.txt cubre todas las fichas publicadas con sus datos y lo enlazan los llms.txt raíz."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'recomendaciones/llms.txt'
SITE = 'https://davidportodiaz.com'


class ReadingLlmsIndexTest(unittest.TestCase):
    def setUp(self):
        self.text = INDEX.read_text(encoding='utf-8')
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        self.books = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.entries = dict(re.findall(r'^- \[[^\]]+\]\((' + re.escape(SITE) + r'/recomendaciones/libros/[^)]+/)\): (.+)$', self.text, re.M))

    def test_every_published_book_has_one_entry_with_its_edition_data(self):
        self.assertEqual(len(self.entries), len(self.books))
        self.assertIn(f'## Libros ({len(self.books)})', self.text)
        for b in self.books:
            entry = self.entries[f"{SITE}/recomendaciones/libros/{b['slug']}/"]
            for value in (*b['autores'], b['editorial'], 'ISBN ' + b['isbn13'], 'Sinopsis de la editorial: '):
                self.assertIn(value, entry, b['id'])
            self.assertTrue((ROOT / 'recomendaciones/libros' / b['slug'] / 'index.html').is_file(), b['id'])

    def test_index_is_plain_attributed_text_without_tracking_links(self):
        self.assertTrue(self.text.startswith('# '))
        self.assertIn('no atribuirlas a David Porto Díaz', self.text)
        self.assertNotIn('amazon.', self.text)
        self.assertNotIn('<', self.text)
        self.assertLess(max(len(line) for line in self.text.splitlines()), 700)

    def test_root_machine_surfaces_link_the_index_and_publication_allows_it(self):
        for name in ('llms.txt', 'llms-full.txt'):
            self.assertIn(SITE + '/recomendaciones/llms.txt', (ROOT / name).read_text(encoding='utf-8'), name)
        self.assertIn("'recomendaciones/llms.txt'", (ROOT / 'scripts/publish-reading-refresh.py').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
