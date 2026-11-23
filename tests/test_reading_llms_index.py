"""El índice recomendaciones/llms.txt cubre todas las fichas publicadas con sus datos y lo enlazan los llms.txt raíz."""
import importlib.util
import json
import sys
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'recomendaciones/llms.txt'
SITE = 'https://davidportodiaz.com'
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
from contrato_libros import incumplen  # noqa: E402
spec = importlib.util.spec_from_file_location('reading_llms_builder', ROOT / 'scripts/build-reading-catalogue.py')
brc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brc)


class ReadingLlmsIndexTest(unittest.TestCase):
    def setUp(self):
        self.text = INDEX.read_text(encoding='utf-8')
        self.data = data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        self.books = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.entries = dict(re.findall(r'^- \[(?:\\.|[^\]\\])+\]\((' + re.escape(SITE) + r'/recomendaciones/libros/[^)]+/)\): (.+)$', self.text, re.M))

    def test_every_published_book_has_one_entry_with_its_edition_data(self):
        self.assertEqual(len(self.entries), len(self.books))
        self.assertIn(f'## Libros ({len(self.books)})', self.text)
        fallos = {}
        for b in self.books:
            entry = self.entries.get(f"{SITE}/recomendaciones/libros/{b['slug']}/")
            if entry is None:
                fallos[b['id']] = 'sin entrada en recomendaciones/llms.txt'
                continue
            label = 'Sinopsis de la editorial: ' if b.get('sinopsis_breve') else 'Descripción: '
            falta = [v for v in (b['autores'][0], b['editorial'], 'ISBN ' + b['isbn13'], label) if v not in entry]
            # Todos los autores, o los que quepan seguidos de «y N más» (antologías).
            if ', '.join(b['autores']) not in entry and not re.search(r' y \d+ más\. ', entry):
                falta.append('autores completos o «y N más»')
            if not (ROOT / 'recomendaciones/libros' / b['slug'] / 'index.html').is_file():
                falta.append('ficha publicada')
            if falta:
                fallos[b['id']] = 'falta en la entrada: ' + ', '.join(falta)
        incumplen('entrada del índice llms con los datos de la edición', fallos)

    def test_index_is_plain_attributed_text_without_tracking_links(self):
        self.assertTrue(self.text.startswith('# '))
        self.assertIn('no atribuirlas a David Porto Díaz', self.text)
        self.assertNotIn('amazon.', self.text)
        self.assertNotIn('<', self.text)
        largas = {}
        for line in self.text.splitlines():
            if len(line) >= 700:
                dueno = next((b['id'] for b in self.books if f"/libros/{b['slug']}/" in line), None)
                largas[dueno or line[:60]] = f'línea de {len(line)} caracteres'
        incumplen('línea del índice llms de menos de 700 caracteres', largas)

    def test_extreme_record_still_fits_one_line(self):
        # Lote 42436110753: una ficha desbordó la línea (1224 caracteres) y se revirtió toda la ingesta.
        base = dict(self.books[0])
        huge = dict(base, id='x-extremo', slug='x-extremo', titulo='Título ' * 60, autores=['Autora Número ' + str(i) for i in range(40)],
                    editorial='Editorial ' * 20, edad_recomendada='De 8 a 12 años ' * 10)
        text = brc.render_llms_index(self.data, [huge], [], [])
        line = next(line for line in text.splitlines() if 'x-extremo' in line)
        self.assertLess(len(line), 700)
        self.assertIn('Autora Número 0', line)
        self.assertRegex(line, r'Autora Número \d+ y \d+ más')

    def test_root_machine_surfaces_link_the_index_and_publication_allows_it(self):
        for name in ('llms.txt', 'llms-full.txt'):
            self.assertIn(SITE + '/recomendaciones/llms.txt', (ROOT / name).read_text(encoding='utf-8'), name)
        self.assertIn("'recomendaciones/llms.txt'", (ROOT / 'scripts/publish-reading-refresh.py').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
