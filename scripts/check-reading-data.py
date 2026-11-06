#!/usr/bin/env python3
"""Validación rápida de los datos reales del catálogo: lo que una carga sin cambios de código puede romper.

La ingesta solo cambia datos (fichas, precios, portadas) y las páginas que se derivan de ellos. El código lo prueba
el Required merge gate en cada PR con la batería completa; repetirla dentro de la ingesta costaba 21 minutos y, si
fallaba, perdía el lote. Aquí van solo los contratos que leen data/reading-catalogue.json o las páginas generadas
(ISBN, autor, formato, precio, enlaces, títulos ≤75, paridad de fichas e índices). build-reading-catalogue.py ya
valida cada libro al construir; esto cubre lo que se ve entre páginas.

    python scripts/check-reading-data.py
"""
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_CONTRACTS = (
    'test_reading_affiliate_card_ux', 'test_reading_card_contract', 'test_reading_catalogue_geo',
    'test_reading_catalogue_navigation_ux', 'test_reading_collection_lastmod', 'test_reading_editorial_shouting',
    'test_reading_formats', 'test_reading_full_synopsis_taxonomy', 'test_reading_itemlist_detail_title_parity',
    'test_reading_llms_index', 'test_reading_multibook_ics_page_parity', 'test_reading_open_graph_book',
    'test_reading_pvp_coherence', 'test_reading_related_books', 'test_reading_taxonomy_derived',
    'test_reading_intake_pipeline.ContractTests.test_catalogue_titles_are_bounded_distinct_and_name_the_author',
)


def main():
    sys.path.insert(0, str(ROOT / 'tests'))
    start = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromNames(DATA_CONTRACTS)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    print(f'datos del catálogo: {result.testsRun} contratos en {time.monotonic() - start:.0f}s')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
