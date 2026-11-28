"""La puerta de datos (scripts/check-reading-data.py) no se queda atrás de la QA de la PR.

16/11: la carga 43805010918 aceptó su lote y la QA offline de la PR falló en un contrato por libro
(test_reading_texts: un libro con un solo módulo) que la puerta no ejecutaba. La puerta aparta los libros que
fallan; la QA de la PR no, así que se perdió el lote entero. Este test descubre por AST todo método que recorre el
catálogo real (`data/reading-catalogue.json`) con aserciones dentro del bucle y exige que esté en la puerta o en
CODIGO, la lista explícita de tests de código con datos de prueba.
"""
import ast
import re
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
    'test_reading_amazon_audit.AmazonAuditTests.test_cover_cap_goes_to_the_books_closest_to_today',
    'test_reading_amazon_audit.AmazonAuditTests.test_books_without_synopsis_not_yet_read_for_it_go_first_closest_first',
    'test_reading_amazon_audit.AmazonAuditTests.test_sin_registro_van_antes_los_libros_sin_sinopsis_aunque_sean_mas_lejanos',
    'test_reading_enrichment.EnrichmentTests.test_editorial_outage_preserves_catalogue_and_allows_independent_refresh',
    'test_reading_intake_multibook_contract.MultiBookContractTests.test_three_independent_pages_one_hub_and_categories',
    'test_reading_intake_multibook_contract.MultiBookContractTests.test_partially_ready_book_does_not_break_other_two',
    'test_reading_intake_pipeline.SourceTests.test_source_hosts_queries_and_isbn_checksums',
    'test_reading_intake_pipeline.ContractTests.test_bad_candidate_isolated_manual_book_pinned_and_repeated_run_noop',
    'test_reading_source_recovery.RecoveryTests.test_concurrent_book_additions_keep_main_and_pending_source_data',
    'test_reading_source_recovery.RecoveryTests.test_existing_book_updates_survive_a_conflicting_main',
    'test_reading_source_recovery.RecoveryTests.test_existing_book_dependencies_and_asset_only_changes_survive',
    'test_reading_source_recovery.RecoveryTests.test_a_book_without_provenance_is_set_aside_and_the_rest_is_recovered',
    'test_reading_source_recovery.RecoveryTests.test_a_legacy_manifest_without_digests_sets_its_books_aside_instead_of_failing',
    'test_reading_texts.ReadingTextsTest.test_git_output_is_read_as_utf8_whatever_the_console_codepage',
    'test_reading_texts.ReadingTextsTest.test_book_page_renders_modules_before_editorial_synopsis',
    'test_presupuesto_sitio.MedidaYRegistro.test_unreadable_or_incomplete_measurement_is_no_measurement',
}
ITERABLES = ('published(', 'libros', 'books')
UN_ARGUMENTO = ('assertTrue', 'assertFalse', 'assertIsNone', 'assertIsNotNone')


def alias_de_libros(metodo):
    """Nombres que, por asignación, guardan el catálogo real o una parte suya (`catalogo = json.loads(<...>
    reading-catalogue.json ...)`, `libros = catalogo['libros']`, `todo = libros`): el iterable se reconoce por su
    origen, no por cómo se llama la variable. Solo se sigue el acceso directo (nombre, índice, atributo); lo que se
    calcula a partir del catálogo con otras funciones ya no es «el catálogo»."""
    asignaciones = [(n.targets, n.value) for n in ast.walk(metodo) if isinstance(n, ast.Assign)]
    alias, antes = set(), None
    while alias != antes:
        antes = set(alias)
        for destinos, valor in asignaciones:
            if clave_ajena(valor):  # `catalogo['categorias']` es parte del catálogo, pero no son libros
                continue
            leido = not isinstance(valor, (ast.List, ast.Tuple, ast.ListComp)) and 'reading-catalogue.json' in ast.unparse(valor)
            if leido or raiz(valor) in alias:  # una lista de rutas que incluye el catálogo no es el catálogo
                alias |= {d.id for d in destinos if isinstance(d, ast.Name)}
    return alias


CLAVES_AJENAS = ('categorias', 'schema_version')  # partes del catálogo que no son libros; una clave desconocida sí cuenta


def clave_ajena(nodo):
    """¿Selecciona `nodo` una parte del catálogo que no son libros (`x['categorias']`, `x.get('categorias')`)?"""
    while isinstance(nodo, (ast.Subscript, ast.Attribute, ast.Call)):
        if isinstance(nodo, ast.Call):
            es_get = isinstance(nodo.func, ast.Attribute) and nodo.func.attr == 'get' and nodo.args
            clave = nodo.args[0] if es_get else None
            nodo = nodo.func.value if es_get else None
        else:
            clave = nodo.slice if isinstance(nodo, ast.Subscript) else None
            nodo = nodo.value
        if isinstance(clave, ast.Constant) and isinstance(clave.value, str):
            return clave.value in CLAVES_AJENAS
    return False


def raiz(nodo):
    """Nombre raíz de `x`, `x['libros']`, `x.libros` o `x['libros'][0]`; None si es otra expresión."""
    while isinstance(nodo, (ast.Subscript, ast.Attribute)):
        nodo = nodo.value
    return nodo.id if isinstance(nodo, ast.Name) else None


def sobre_libros(iterable, alias):
    """¿Recorre libros este iterable (por las claves conocidas o por un alias asignado desde el catálogo)?"""
    texto = ast.unparse(iterable)
    return any(k in texto for k in ITERABLES) or raiz(iterable) in alias


def mensaje(llamada):
    """El mensaje de una aserción (posicional tras sus operandos o `msg=`), o None."""
    nombre = llamada.func.attr
    minimo = 1 if nombre in UN_ARGUMENTO else 2
    if len(llamada.args) > minimo:
        return llamada.args[minimo]
    return next((k.value for k in llamada.keywords if k.arg == 'msg'), None)


def nombra_el_libro(texto, variables):
    """¿El mensaje incluye el id del libro del bucle (`b['id']`, `b.get('id')`, `b["id"]`)?"""
    # con límite de nombre: `other_book['id']` no nombra a `book` aunque lo contenga
    return any(re.search(rf"(?<![\w.]){re.escape(v)}(\['id'\]|\.get\('id'\))", texto) for v in variables)


def asserts_sin_mensaje(metodo):
    """Aserciones dentro de un bucle sobre libros cuyo mensaje no nombra el id del libro: su fallo no se puede
    atribuir y la cuarentena (reading_quarantine.flagged_books) no puede apartarlo, así que para el lote entero.
    Una URL o un texto fijo no bastan: hace falta el id."""
    alias = alias_de_libros(metodo)
    for bucle in (n for n in ast.walk(metodo) if isinstance(n, ast.For) and sobre_libros(n.iter, alias)):
        variables = {x.id for x in ast.walk(bucle.target) if isinstance(x, ast.Name)}
        for x in ast.walk(bucle):
            nombre = getattr(getattr(x, 'func', None), 'attr', '')
            if isinstance(x, ast.Call) and nombre.startswith('assert') and nombre != 'assertRaises':
                texto = mensaje(x)
                if texto is None or not nombra_el_libro(ast.unparse(texto), variables):
                    yield f'{metodo.name}:{x.lineno} {nombre}'


def metodos(solo_catalogo=False):
    """Métodos test_* de tests/ (con `solo_catalogo`, solo de los módulos que leen el catálogo real)."""
    for fichero in sorted((ROOT / 'tests').glob('test_*.py')):
        fuente = fichero.read_text(encoding='utf-8', errors='ignore')
        if solo_catalogo and 'reading-catalogue.json' not in fuente:
            continue
        for clase in (n for n in ast.parse(fuente).body if isinstance(n, ast.ClassDef)):
            for metodo in (n for n in clase.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test')):
                yield f'{fichero.stem}.{clase.name}.{metodo.name}', metodo


def recorre_libros(metodo):
    """¿Hay un bucle (o comprensión) sobre libros con aserciones en su ámbito?"""
    alias = alias_de_libros(metodo)
    for bucle in (n for n in ast.walk(metodo) if isinstance(n, (ast.For, ast.comprehension))):
        ambito = bucle if isinstance(bucle, ast.For) else metodo
        if sobre_libros(bucle.iter, alias) and any(
                isinstance(x, ast.Call) and getattr(x.func, 'attr', '').startswith('assert') for x in ast.walk(ambito)):
            return True
    return False


def por_libro():
    """Métodos test_* de módulos que leen el catálogo real con un bucle sobre libros y aserciones dentro."""
    return [nombre for nombre, metodo in metodos(solo_catalogo=True) if recorre_libros(metodo)]


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

    def test_la_guardia_exige_el_id_y_sigue_los_alias(self):
        def metodo(cuerpo):
            return ast.parse('def test_x(self):\n' + cuerpo).body[0]

        bueno = "    catalogo = json.loads(ruta.read_text())\n    for b in catalogo['libros']:\n        self.assertTrue(b['ok'], f\"{b['id']}: mal\")\n"
        self.assertEqual(list(asserts_sin_mensaje(metodo(bueno))), [])
        for malo in ("        self.assertTrue(b['ok'], 'mensaje fijo')\n",
                     "        self.assertTrue(b['ok'], f\"https://x/{b['slug']}\")\n",
                     "        self.assertTrue(b['ok'])\n",
                     "        self.assertTrue(b['ok'], f\"{ab['id']}: otro libro\")\n"):
            with self.subTest(malo=malo):
                fuente = bueno.split('        self.')[0] + malo
                self.assertEqual(len(list(asserts_sin_mensaje(metodo(fuente)))), 1, 'sin id del libro no vale')
        alias = "    cat = json.loads((ROOT / 'data/reading-catalogue.json').read_text())\n    todo = cat['x']\n    for b in todo:\n        self.assertTrue(b)\n"
        self.assertTrue(recorre_libros(metodo(alias)), 'el alias asignado desde el catálogo cuenta')
        categorias = ("    cats = json.loads((ROOT / 'data/reading-catalogue.json').read_text())['categorias']\n"
                      "    ids = {c['id'] for c in cats}\n    self.assertTrue(ids)\n")
        self.assertFalse(recorre_libros(metodo(categorias)), 'recorrer las categorías del catálogo no es recorrer libros')
        ajeno = "    filas = [1, 2]\n    for b in filas:\n        self.assertTrue(b)\n"
        self.assertFalse(recorre_libros(metodo(ajeno)), 'un bucle sobre otra cosa no es un contrato por libro')

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
