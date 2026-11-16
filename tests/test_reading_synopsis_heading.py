"""P0-7 (H7): ninguna ficha titula «Sinopsis de la editorial» lo que no lo es.

Recorre todas las fichas publicadas generadas: sin sinopsis_breve no hay ese título.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SynopsisHeadingTest(unittest.TestCase):
    def test_no_false_editorial_synopsis(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        bad = []
        for b in data['libros']:
            if b.get('estado') != 'publicado' or b.get('sinopsis_breve'):
                continue
            page = ROOT / 'recomendaciones/libros' / b['slug'] / 'index.html'
            if page.exists() and 'Sinopsis de la editorial' in page.read_text(encoding='utf-8'):
                bad.append(b['slug'])
        self.assertEqual(bad, [], f'{len(bad)} fichas sin sinopsis_breve con «Sinopsis de la editorial»: {bad[:5]}')


if __name__ == '__main__':
    unittest.main()
