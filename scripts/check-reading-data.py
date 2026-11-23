#!/usr/bin/env python3
"""Validación rápida de los datos reales del catálogo: lo que una carga sin cambios de código puede romper.

La ingesta solo cambia datos (fichas, precios, portadas) y las páginas que se derivan de ellos. El código lo prueba
el Required merge gate en cada PR con la batería completa; repetirla dentro de la ingesta costaba 21 minutos y, si
fallaba, perdía el lote. Aquí van solo los contratos que leen data/reading-catalogue.json o las páginas generadas
(ISBN, autor, formato, precio, enlaces, títulos ≤75, paridad de fichas e índices). build-reading-catalogue.py ya
valida cada libro al construir; esto cubre lo que se ve entre páginas.

    python scripts/check-reading-data.py
    python scripts/check-reading-data.py --fallos f.json   # además deja los fallos en JSON (la carga aparta sus libros)
"""
import json
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_CONTRACTS = (
    'test_reading_affiliate_card_ux', 'test_reading_card_contract', 'test_reading_catalogue_geo',
    'test_reading_catalogue_navigation_ux', 'test_reading_collection_lastmod', 'test_reading_editorial_shouting',
    'test_reading_formats', 'test_reading_text_encoding', 'test_reading_full_synopsis_taxonomy', 'test_reading_itemlist_detail_title_parity',
    'test_reading_llms_index', 'test_reading_multibook_ics_page_parity', 'test_reading_open_graph_book',
    'test_reading_pvp_coherence', 'test_reading_related_books', 'test_reading_taxonomy_derived',
    'test_reading_intake_pipeline.ContractTests.test_catalogue_titles_are_bounded_distinct_and_name_the_author',
    'test_reading_author_split', 'test_published_book_author_parity', 'test_published_book_jsonld_identity_parity',
    'test_published_isbn_schema_parity', 'test_book_title_schema_consistency', 'test_reading_category_invariants',
    # 16/11: la carga 43805010918 salió roja en la QA de la PR por un libro con un solo módulo (isbn-9791388205675)
    # que esta puerta no miraba, y se perdió el lote entero en vez de apartar ese libro. Los métodos que recorren
    # el catálogo real con aserciones por libro entran aquí; tests/test_check_reading_data_cobertura.py lo vigila.
    'test_reading_texts.ReadingTextsTest.test_every_published_book_gets_its_own_reader_module',
    'test_reading_texts.ReadingTextsTest.test_families_and_modules_follow_the_evidence',
    'test_reading_texts.ReadingTextsTest.test_affines_share_audience_and_are_described_by_content_not_labels',
    'test_reading_texts.ReadingTextsTest.test_affines_survive_catalogue_growth',
    'test_atlas_integration_real_catalogue.RealCatalogueBridge.test_every_published_book_resolves_to_an_existing_page',
    'test_book_modified_date_parity.ModifiedDateParity.test_dates_match_published_pages',
    'test_reading_taxonomy_children.ChildrenGenreTests.test_published_catalogue_has_no_adult_genre_on_children_or_seasons',
)
# Familias que solo leen datos: entran todas, también las que se añadan, para que esta lista no se quede atrás de la
# puerta (faltaban las de mercado y una PR nocturna salió roja por precios sin precios_amazon_revision).
DATA_FAMILIES = ('test_market_*.py', 'test_*_smoke.py')


def contracts():
    found = {f.stem for pattern in DATA_FAMILIES for f in (ROOT / 'tests').glob(pattern)}
    return list(DATA_CONTRACTS) + sorted(found - set(DATA_CONTRACTS))


class Resultado(unittest.TextTestResult):
    """Guarda los libros que declara cada contrato con `contrato_libros.incumplen` (R4-2b), por objeto de test:
    dos subTests con los mismos parámetros comparten `test.id()` y uno pisaría los libros del otro."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.libros = {}

    def _guardar(self, test, err):
        from contrato_libros import Incumplen
        if err is not None and isinstance(err[1], Incumplen):
            self.libros[id(test)] = {'regla': err[1].regla, 'libros': err[1].libros}

    def addFailure(self, test, err):
        self._guardar(test, err)
        super().addFailure(test, err)

    def addError(self, test, err):  # también un `incumplen` desde setUpClass
        self._guardar(test, err)
        super().addError(test, err)

    def addSubTest(self, test, subtest, err):
        self._guardar(subtest, err)
        super().addSubTest(test, subtest, err)


def fallos(result):
    """[{test, texto}] y, si el contrato los declaró, {regla, libros: {id: motivo}}."""
    return [{'test': test.id(), 'texto': text, **result.libros.get(id(test), {})}
            for test, text in result.failures + result.errors]


def main():
    sys.path.insert(0, str(ROOT / 'tests'))
    start = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromNames(contracts())
    result = unittest.TextTestRunner(verbosity=1, resultclass=Resultado).run(suite)
    print(f'datos del catálogo: {result.testsRun} contratos en {time.monotonic() - start:.0f}s')
    if '--fallos' in sys.argv:
        path = Path(sys.argv[sys.argv.index('--fallos') + 1])
        path.write_text(json.dumps(fallos(result), ensure_ascii=False, indent=1), encoding='utf-8')
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    raise SystemExit(main())
