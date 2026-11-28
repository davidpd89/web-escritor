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
import os
import subprocess
import tempfile
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_CONTRACTS = (
    'test_reading_affiliate_card_ux', 'test_reading_card_contract', 'test_reading_catalogue_geo',
    'test_reading_catalogue_navigation_ux', 'test_reading_collection_lastmod', 'test_reading_editorial_shouting',
    'test_reading_formats', 'test_reading_text_encoding', 'test_reading_title_only_fiction.PublishedCatalogueTests', 'test_reading_full_synopsis_taxonomy', 'test_reading_itemlist_detail_title_parity',
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
# Contratos en script (tests/test-*.py, no unittest) que leen el catálogo o lo generado a partir de él. 23/11: la carga
# de las 00:17 abrió su PR con un título de ficha de 206 caracteres; tests/test-page-order.py (solo en la puerta de
# la PR) lo rechazó 2,5 h después y se perdió la noche. Entran todos los que lean estos rastros, también los que se
# añadan; SCRIPTS_CODIGO son los que prueban código con datos propios o tardan minutos (el código lo prueba la puerta).
SCRIPT_RASTROS = ('reading-catalogue.json', 'page-order', 'recomendaciones')
SCRIPTS_CODIGO = {
    'test-reading-publication.py', 'test-reading-import.py', 'test-reading-catalogue.py',
    'test-publish-pages-superseded.py', 'test-publish-qa-refresh.py', 'test-ci-content-lane.py',
}
SCRIPT_LIMITE = 900  # segundos por script


def script_contracts(root=ROOT):
    return sorted(f.name for f in (root / 'tests').glob('test-*.py')
                  if f.name not in SCRIPTS_CODIGO
                  and any(r in f.read_text(encoding='utf-8', errors='ignore') for r in SCRIPT_RASTROS))


def run_scripts(root=ROOT, names=None, workers=4):
    """Corre los contratos en script de 4 en 4; devuelve [{test, texto}] de los que fallan (vacío si pasan)."""
    def one(name):
        with tempfile.TemporaryDirectory() as tmp:
            fichero = Path(tmp) / 'libros.json'
            env = {**os.environ, 'CONTRATO_LIBROS_FICHERO': str(fichero)}
            try:
                done = subprocess.run([sys.executable, str(root / 'tests' / name)], cwd=root, capture_output=True,
                                      text=True, encoding='utf-8', errors='replace', timeout=SCRIPT_LIMITE, env=env)
            except subprocess.TimeoutExpired:
                return {'test': 'tests/' + name, 'texto': f'sin terminar en {SCRIPT_LIMITE} s'}
            if done.returncode == 0:
                return None
            libros = json.loads(fichero.read_text(encoding='utf-8')) if fichero.is_file() else {}
            return {'test': 'tests/' + name, 'texto': (done.stdout + done.stderr)[-1500:], **libros}
    with ThreadPoolExecutor(workers) as pool:
        return [f for f in pool.map(one, script_contracts(root) if names is None else names) if f]


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


def load(names):
    """(suite, [{test, texto}] de los que no cargan). Uno por uno: 28/11 la carga 46117573426 murió sin escribir
    sus fallos porque un contrato importaba un script que hacía sys.exit(1) al importarse; ni ese contrato apartó
    sus libros ni los demás pudieron apartar los suyos. Un contrato que no carga es un fallo más, no el final."""
    suite, broken = unittest.TestSuite(), []
    for name in names:
        try:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
        except (Exception, SystemExit) as exc:  # SystemExit no es Exception; Ctrl+C sí debe parar
            broken.append({'test': name, 'texto': f'no carga: {type(exc).__name__}: {exc}'[:1500]})
    return suite, broken


def main():
    sys.path.insert(0, str(ROOT / 'tests'))
    start = time.monotonic()
    suite, broken = load(contracts())
    for f in broken:
        print(f"FALLA {f['test']}:\n{f['texto']}", flush=True)
    result = unittest.TextTestRunner(verbosity=1, resultclass=Resultado).run(suite)
    print(f'datos del catálogo: {result.testsRun} contratos en {time.monotonic() - start:.0f}s')
    start = time.monotonic()
    scripts = run_scripts()
    for f in scripts:
        # Un script que no termina a tiempo no es un fallo determinista: sin «FALLA» la puerta sí lo reintenta.
        marca = 'TIEMPO' if f['texto'].startswith('sin terminar') else 'FALLA'
        print(f"{marca} {f['test']}:\n{f['texto']}", flush=True)
    print(f'datos del catálogo: {len(script_contracts())} contratos en script en {time.monotonic() - start:.0f}s')
    if '--fallos' in sys.argv:
        path = Path(sys.argv[sys.argv.index('--fallos') + 1])
        path.write_text(json.dumps(broken + fallos(result) + scripts, ensure_ascii=False, indent=1), encoding='utf-8')
    return 0 if result.wasSuccessful() and not scripts and not broken else 1

if __name__ == '__main__':
    raise SystemExit(main())
