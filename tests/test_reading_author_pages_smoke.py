"""Todo autor con ≥2 libros publicados (con ficha editorial https) tiene ficha y página de autor.

Entra en la puerta de datos de la carga por el patrón `test_*_smoke.py` (scripts/check-reading-data.py). La carga
crea las fichas en assemble() (scripts/backfill-reading-author-pages.py) antes de generar; si aun así falta alguna,
el fallo nombra los libros de ese autor para que la cuarentena los aparte y el resto del lote siga.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'scripts'))
from contrato_libros import incumplen  # noqa: E402
from reading_intake_pipeline import AUTHOR_PAGE_MIN_BOOKS, NO_PAGE_AUTHORS  # noqa: E402


class AuthorPagesSmoke(unittest.TestCase):
    def test_every_author_with_enough_books_has_a_page(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        authors = {a['nombre']: a for a in json.loads((ROOT / 'data/reading-authors.json').read_text(encoding='utf-8'))['autores']}
        by_author = {}
        for b in catalogue['libros']:
            if b['estado'] == 'publicado' and str(b.get('fuente_bibliografica_url', '')).startswith('https://'):
                for name in b['autores']:
                    by_author.setdefault(name, []).append(b['id'])
        bad = {}
        for name, ids in by_author.items():
            if len(ids) < AUTHOR_PAGE_MIN_BOOKS or name in NO_PAGE_AUTHORS or not name.strip():
                continue
            a = authors.get(name)
            if not a:
                reason = f'autor «{name}» con {len(ids)} libros sin ficha en data/reading-authors.json'
            elif not (ROOT / 'recomendaciones/autores' / a['slug'] / 'index.html').exists():
                reason = f'autor «{name}» sin página generada'
            else:
                continue
            bad.update({i: reason for i in ids})
        incumplen('autor con varios libros sin página', bad)


if __name__ == '__main__':
    unittest.main()
