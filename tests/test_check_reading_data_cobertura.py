"""La puerta de datos (scripts/check-reading-data.py) no se queda atrás de la QA de la PR.

16/11: la carga 43805010918 aceptó su lote y la QA offline de la PR falló en un contrato por libro
(test_reading_texts: un libro con un solo módulo) que la puerta no ejecutaba. La puerta aparta los libros que
fallan; la QA de la PR no, así que se perdió el lote entero. Este test descubre por AST todo método que recorre el
catálogo real (`data/reading-catalogue.json`) con aserciones dentro del bucle y exige que esté en la puerta o en
CODIGO, la lista explícita de tests de código con datos de prueba.
"""
import ast
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_reading_data', ROOT / 'scripts/check-reading-data.py')
puerta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(puerta)

# Recorren libros de fixtures o de un repo temporal, no el catálogo publicado: un fallo es de código, no de un libro.
CODIGO = {
    'test_reading_amazon_audit.AmazonAuditTests.test_every_published_book_is_due_oldest_first_without_a_cap',
    'test_reading_amazon_audit.AmazonAuditTests.test_cover_follows_the_book_in_main_not_the_kind_stored_in_the_record',
    'test_reading_enrichment.EnrichmentTests.test_editorial_outage_preserves_catalogue_and_allows_independent_refresh',
    'test_reading_intake_multibook_contract.MultiBookContractTests.test_three_independent_pages_one_hub_and_categories',
    'test_reading_intake_multibook_contract.MultiBookContractTests.test_partially_ready_book_does_not_break_other_two',
    'test_reading_intake_pipeline.SourceTests.test_source_hosts_queries_and_isbn_checksums',
    'test_reading_intake_pipeline.ContractTests.test_bad_candidate_isolated_manual_book_pinned_and_repeated_run_noop',
    'test_reading_source_recovery.RecoveryTests.test_concurrent_book_additions_keep_main_and_pending_source_data',
    'test_reading_source_recovery.RecoveryTests.test_existing_book_updates_survive_a_conflicting_main',
    'test_reading_source_recovery.RecoveryTests.test_existing_book_dependencies_and_asset_only_changes_survive',
    'test_reading_texts.ReadingTextsTest.test_git_output_is_read_as_utf8_whatever_the_console_codepage',
    'test_reading_texts.ReadingTextsTest.test_book_page_renders_modules_before_editorial_synopsis',
}
ITERABLES = ('published(', 'libros', 'books')
UN_ARGUMENTO = ('assertTrue', 'assertFalse', 'assertIsNone', 'assertIsNotNone')


def asserts_sin_mensaje(metodo):
    """Aserciones dentro de un bucle sobre libros sin mensaje: su fallo no nombra el libro y la cuarentena
    (reading_quarantine.flagged_books) no puede apartarlo, así que para el lote entero."""
    for bucle in (n for n in ast.walk(metodo) if isinstance(n, ast.For) and any(k in ast.unparse(n.iter) for k in ITERABLES)):
        for x in ast.walk(bucle):
            nombre = getattr(getattr(x, 'func', None), 'attr', '')
            if isinstance(x, ast.Call) and nombre.startswith('assert') and nombre != 'assertRaises':
                minimo = 1 if nombre in UN_ARGUMENTO else 2
                if len(x.args) <= minimo and not any(k.arg == 'msg' for k in x.keywords):
                    yield f'{metodo.name}:{x.lineno} {nombre}'


def metodos():
    for fichero in sorted((ROOT / 'tests').glob('test_*.py')):
        fuente = fichero.read_text(encoding='utf-8', errors='ignore')
        for clase in (n for n in ast.parse(fuente).body if isinstance(n, ast.ClassDef)):
            for metodo in (n for n in clase.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test')):
                yield f'{fichero.stem}.{clase.name}.{metodo.name}', metodo


def por_libro():
    """Métodos test_* de módulos que leen el catálogo real con un bucle sobre libros y aserciones dentro."""
    for fichero in sorted((ROOT / 'tests').glob('test_*.py')):
        fuente = fichero.read_text(encoding='utf-8', errors='ignore')
        if 'reading-catalogue.json' not in fuente:
            continue
        for clase in (n for n in ast.parse(fuente).body if isinstance(n, ast.ClassDef)):
            for metodo in (n for n in clase.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test')):
                for bucle in (n for n in ast.walk(metodo) if isinstance(n, (ast.For, ast.comprehension))):
                    ambito = bucle if isinstance(bucle, ast.For) else metodo
                    asserts = any(isinstance(x, ast.Call) and getattr(x.func, 'attr', '').startswith('assert')
                                  for x in ast.walk(ambito))
                    if asserts and any(k in ast.unparse(bucle.iter) for k in ITERABLES):
                        yield f'{fichero.stem}.{clase.name}.{metodo.name}'
                        break


class CoberturaPuertaTest(unittest.TestCase):
    def test_todo_contrato_por_libro_esta_en_la_puerta(self):
        cubiertos = set(puerta.contracts())

        def en_puerta(nombre):
            partes = nombre.split('.')
            return any('.'.join(partes[:i]) in cubiertos for i in range(1, len(partes) + 1))

        fuera = [m for m in por_libro() if not en_puerta(m) and m not in CODIGO]
        self.assertEqual(fuera, [], 'contratos por libro que la puerta no ejecuta: añadirlos a DATA_CONTRACTS '
                                    '(o a CODIGO si recorren datos de prueba)')

    def test_la_lista_de_codigo_no_se_pudre(self):
        vistos = set(por_libro())
        self.assertEqual(sorted(CODIGO - vistos), [], 'métodos en CODIGO que ya no existen o no recorren libros')

    def test_los_contratos_por_libro_nombran_el_libro(self):
        por_metodo = [n for n in puerta.DATA_CONTRACTS if n.count('.') == 2]
        sin = [f'{n} {a}' for n, m in metodos() if n in por_metodo for a in asserts_sin_mensaje(m)]
        self.assertEqual(sin, [], 'añadir el id del libro como mensaje de la aserción')

    def test_los_contratos_de_la_puerta_existen(self):
        import sys
        sys.path.insert(0, str(ROOT / 'tests'))
        for nombre in puerta.DATA_CONTRACTS:
            if nombre.count('.') == 2:
                modulo, clase, metodo = nombre.split('.')
                fuente = (ROOT / 'tests' / f'{modulo}.py').read_text(encoding='utf-8')
                self.assertIn(f'class {clase}', fuente, nombre)
                self.assertIn(f'def {metodo}(', fuente, nombre)


if __name__ == '__main__':
    unittest.main()
