"""Todo autor con ≥2 libros publicados (con ficha editorial https) tiene ficha de autor y, por tanto, página.

Antes del 28/11 solo la ingesta editorial creaba fichas: los libros que entraban por Amazon dejaban sin página a
1.120 autores con varios libros, justo los que responden «último/próximo libro de X»."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from reading_intake_pipeline import ensure_author_records  # noqa: E402


def book(i, authors, source='https://editorial.example/ficha'):
    return {'id': f'lib-{i:04d}', 'estado': 'publicado', 'titulo': f'Libro {i}', 'autores': authors, 'fuente_bibliografica_url': source}


class EnsureAuthorRecordsTest(unittest.TestCase):
    def test_creates_only_missing_authors_with_enough_books(self):
        catalogue = {'libros': [book(1, ['Ana Pérez']), book(2, ['Ana Pérez', 'Varios autores']), book(3, ['Varios autores']),
                                book(4, ['Solo Uno']), book(5, ['Ya Existe']), book(6, ['Ya Existe']),
                                book(7, ['Sin Fuente'], source=''), book(8, ['Sin Fuente'], source='')]}
        payload = {'autores': [{'slug': 'ya-existe', 'nombre': 'Ya Existe', 'tipo': 'bibliografico'}]}
        added = ensure_author_records(payload, catalogue, '2026-11-28')
        self.assertEqual(added, ['Ana Pérez'])
        record = payload['autores'][-1]
        self.assertEqual(record['slug'], 'ana-perez')
        self.assertEqual(record['tipo'], 'bibliografico')
        self.assertEqual(len(record['fuentes']), 2)
        self.assertTrue(all(s['url'].startswith('https://') for s in record['fuentes']))
        self.assertGreaterEqual(len(record['descripcion']), 60)
        self.assertEqual(ensure_author_records(payload, catalogue, '2026-11-28'), [])  # idempotente

    def test_slug_clash_gets_a_stable_suffix(self):
        catalogue = {'libros': [book(1, ['Ana Perez']), book(2, ['Ana Perez'])]}
        payload = {'autores': [{'slug': 'ana-perez', 'nombre': 'Ana Pérez', 'tipo': 'bibliografico'}]}
        ensure_author_records(payload, catalogue, '2026-11-28')
        self.assertRegex(payload['autores'][-1]['slug'], r'^ana-perez-[0-9a-f]{8}$')


if __name__ == '__main__':
    unittest.main()
