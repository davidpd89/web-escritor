"""Clase de fallo del 14/11: el barrido de precios empezó a escribir `no_lectura` en las fichas sin darlo de alta en
BOOK_FIELDS y la validación («campos desconocidos») tumbó dos lotes nocturnos enteros.

Todo campo que un script escribe en una ficha (`book[...] = …`, `book.setdefault(...)`) debe estar en el esquema o
ser una marca transitoria que se consume antes de validar, y
el error de validación debe nombrar el libro para que la cuarentena aparte solo ese libro."""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('build_reading_catalogue_fields', ROOT / 'scripts/build-reading-catalogue.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
import reading_quarantine  # noqa: E402

WRITE = re.compile(r"\b(?:book|libro)(?:\[['\"](\w+)['\"]\]\s*=(?!=)|\.setdefault\(\s*['\"](\w+)['\"])")
# Escrituras en objetos que no son fichas del catálogo, o que solo reescriben un campo si ya existe.
NOT_CATALOGUE = {
    ('reading_intake_fetch.py', 'fuente'),           # candidato de la ingesta, no ficha publicada
    ('reading_amazon_market.py', 'encuadernacion'),  # solo `if book.get('encuadernacion')`: nunca lo crea
    # Marca transitoria: reading_quarantine.repair_retire_non_reading la consume (pop) antes de validar (#1310).
    ('reading_amazon_market.py', 'no_lectura'),
}


class BookFieldsTest(unittest.TestCase):
    def test_todo_campo_escrito_en_una_ficha_esta_en_el_esquema(self):
        unknown = []
        for path in sorted((ROOT / 'scripts').rglob('*.py')):
            for n, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
                for a, b in WRITE.findall(line):
                    field = a or b
                    if field not in build.BOOK_FIELDS and (path.name, field) not in NOT_CATALOGUE:
                        unknown.append(f'{path.relative_to(ROOT)}:{n} {field}')
        self.assertEqual(unknown, [], 'Añade el campo a BOOK_FIELDS (build-reading-catalogue.py) o no lo escribas en la ficha')

    def test_la_marca_no_lectura_se_consume_antes_de_validar(self):
        books = [{'id': 'x', 'titulo': 'Novela', 'estado': 'publicado', 'no_lectura': 'actividades'}]
        reading_quarantine.repair_retire_non_reading(books, ROOT, '2026-11-14')
        self.assertNotIn('no_lectura', books[0])
        self.assertEqual(books[0]['estado'], 'borrador')

    def test_campo_desconocido_nombra_al_libro_y_la_cuarentena_lo_reconoce(self):
        data = {'schema_version': 1, 'categorias': [], 'libro_categorias': [],
                'libros': [{'id': 'libro-raro', 'campo_nuevo': 1}]}
        with self.assertRaises(build.ValidationError) as caught:
            build.validate(data, ROOT)
        message = str(caught.exception)
        self.assertIn('campo_nuevo', message)
        self.assertEqual(reading_quarantine.culprit(message, data), 'libro-raro')


if __name__ == '__main__':
    unittest.main()
