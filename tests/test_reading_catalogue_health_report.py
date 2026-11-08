"""Monitor de salud del catálogo: solo informa, persiste para comparar y no da falsos positivos."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('health', ROOT / 'scripts/catalogue-health-report.py')
health = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health)


def book(n, **extra):
    base = {'id': f'libro-{n}', 'titulo': f'Libro {n}', 'isbn13': f'978000000000{n}', 'estado': 'publicado',
            'fecha_publicacion': '2099-01-01', 'portada_local': f'/assets/reading-covers/libro-{n}.webp',
            'portada_fuente_url': 'https://m.media-amazon.com/images/I/x.jpg', 'sinopsis_breve': 'Texto.',
            'formatos_compra': [{'formato': 'tapa blanda', 'precio_centimos': 1990, 'url': 'https://www.amazon.es/dp/X'}]}
    return {**base, **extra}


class HealthReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'data').mkdir()
        (self.root / 'assets/reading-covers').mkdir(parents=True)
        for n in range(4):
            (self.root / f'assets/reading-covers/libro-{n}.webp').write_bytes(b'x')

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, books):
        (self.root / 'data/reading-catalogue.json').write_text(json.dumps({'libros': books}), encoding='utf-8')

    def run_report(self):
        with mock.patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': ''}), mock.patch('builtins.print'):
            self.assertEqual(health.main(['--root', str(self.root)]), 0)
        return json.loads((self.root / '.ci/salud-catalogo/informe.json').read_text(encoding='utf-8'))

    def test_site_paths_of_existing_covers_are_not_reported_missing(self):
        # Antes: «/assets/...» se unía como ruta absoluta y salían los 2241 libros como portada sin fichero.
        self.write([book(0), book(1, portada_local='/assets/reading-covers/no-existe.webp')])
        sections = self.run_report()['secciones']
        self.assertEqual(sections['portada_sin_fichero']['total'], 1)
        self.assertEqual(sections['portada_sin_fichero']['muestra'][0]['id'], 'libro-1')

    def test_counts_each_known_failure(self):
        self.write([
            book(0),
            book(1, formatos_compra=[{'formato': 'ebook', 'url': 'https://www.amazon.es/dp/Y'}]),
            book(2, formatos_compra=[]),
            book(3, sinopsis_breve=''),
            book(4, estado='borrador', sinopsis_breve='', formatos_compra=[]),
        ])
        sections = self.run_report()['secciones']
        self.assertEqual(sections['formatos_sin_precio']['total'], 1)
        self.assertEqual(sections['formatos_sin_precio']['por_formato'], {'ebook': 1})
        self.assertEqual(sections['sin_formatos_de_compra']['total'], 1)
        self.assertEqual(sections['sin_texto']['total'], 1)
        self.assertEqual(sections['sin_texto']['proximos'], 1)

    def test_own_text_file_counts_as_text(self):
        (self.root / 'data/reading-texts').mkdir()
        (self.root / 'data/reading-texts/isbn-9780000000000.json').write_text('{}', encoding='utf-8')
        self.write([book(0, sinopsis_breve='')])
        self.assertEqual(self.run_report()['secciones']['sin_texto']['total'], 0)

    def test_report_persists_in_catalogue_state_and_compares_next_night(self):
        self.write([book(0, formatos_compra=[])])
        self.run_report()
        kept = self.root / '.local/catalogo/salud.json'
        self.assertTrue(kept.exists())
        # .ci/ no sobrevive entre ejecuciones de Actions: la comparación sale de la copia en el estado.
        (self.root / '.ci/salud-catalogo/informe.json').unlink()
        self.write([book(0, formatos_compra=[]), book(1, formatos_compra=[])])
        report = self.run_report()
        self.assertEqual(report['cambio']['sin_formatos_de_compra'], 1)
        self.assertIn('+1', (self.root / '.ci/salud-catalogo/resumen.md').read_text(encoding='utf-8'))

    def test_state_branch_carries_the_report(self):
        import catalogo_estado
        self.assertIn('salud.json', catalogo_estado.FILES)

    def test_amazon_check_separates_opportunities_from_real_gaps(self):
        books = [book(0, fecha_publicacion='2026-11-08'), book(1, fecha_publicacion='2026-11-09')]
        answers = {'libro-0': 'https://m.media-amazon.com/images/I/a.jpg', 'libro-1': None}
        with mock.patch('reading_amazon_market.item_cover_url', side_effect=lambda b, _: answers[b['id']]):
            from datetime import date
            result = health.ask_amazon(books, lambda b: {}, 10, date(2026, 11, 8))
        self.assertEqual((result['amazon_la_tiene'], result['amazon_no_la_tiene']), (1, 1))
        self.assertEqual(result['oportunidades'][0]['id'], 'libro-0')

    def test_amazon_errors_never_raise(self):
        def boom(_):
            raise RuntimeError('eligibility: cuenta no elegible')
        result = health.ask_amazon([book(0), book(1)], boom, 10, __import__('datetime').date(2026, 11, 8))
        self.assertEqual(result['consultados'], 0)
        self.assertEqual(sum(result['errores'].values()), 1)

    def test_nightly_refresh_never_fails_because_of_the_report(self):
        spec = importlib.util.spec_from_file_location('refresh', ROOT / 'scripts/refresh-reading-catalogue.py')
        refresh = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(refresh)
        with mock.patch.object(refresh.subprocess, 'run', side_effect=OSError('sin python')), mock.patch('builtins.print'):
            refresh.health_report({})
        with mock.patch.object(refresh.subprocess, 'run') as run:
            refresh.health_report({'salud_catalogo': {'consultas_amazon': 7}})
        self.assertFalse(run.call_args.kwargs['check'])
        self.assertIn('7', run.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
