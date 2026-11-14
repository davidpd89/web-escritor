"""La importación de la hoja reproduce el catálogo: lo mismo que content-index-check, antes de abrir la PR.

12/11 (#43184625068): `import-reading-sheet.py --check` solo corría en la CI de la PR y tumbó la carga por
«Libro automático sin registro de ingesta: isbn-9791399280128». Como contrato de datos (familia *_smoke) corre en
check-reading-data antes de la PR y nombra TODOS los libros afectados, no solo el primero: la carga los aparta.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('import_reading_sheet', ROOT / 'scripts/import-reading-sheet.py')
sheet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sheet)


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def unregistered(catalogue, state):
    """Libros automáticos (isbn-*) sin el registro que exige la importación (misma regla, sheet.has_intake_record)."""
    return [b['id'] for b in catalogue['libros'] if b['id'].startswith('isbn-') and not sheet.has_intake_record(b, state)]


class SheetImportReproducesCatalogue(unittest.TestCase):
    def test_every_automatic_book_has_its_intake_record(self):
        state_path = ROOT / 'data/reading-intake-state.json'
        state = read('data/reading-intake-state.json') if state_path.exists() else {'items': {}}
        missing = unregistered(read('data/reading-catalogue.json'), state)
        self.assertEqual(missing, [], 'Libros automáticos sin registro de ingesta: ' + ' '.join(missing))

    def test_sheet_import_reproduces_the_catalogue(self):
        catalogue = read('data/reading-catalogue.json')
        try:
            data, _ = sheet.convert(read('data/reading-sheet-snapshot.json'), read('data/reading-import-review.json'),
                                    json.loads(json.dumps(catalogue)), ROOT)
        except ValueError as exc:
            self.fail(str(exc))
        if data != catalogue:
            got = {b['id']: b for b in data['libros']}
            want = {b['id']: b for b in catalogue['libros']}
            differ = sorted(i for i in got.keys() | want.keys() if got.get(i) != want.get(i))
            self.fail('Importación desactualizada: ' + (' '.join(differ[:50]) or 'cambian tablas fuera de libros'))


class UnregisteredRule(unittest.TestCase):
    def test_names_every_automatic_book_without_record(self):
        catalogue = {'libros': [{'id': 'lib-0001'}, {'id': 'isbn-1', 'isbn13': '1'}, {'id': 'isbn-2', 'isbn13': '2'},
                                {'id': 'isbn-3', 'isbn13': '3'}]}
        state = {'items': {'isbn13:1': {'estado_ingesta': 'publicado', 'libro_id': 'isbn-1'},
                           'isbn13:2': {'estado_ingesta': 'pendiente', 'libro_id': 'isbn-2'}}}
        self.assertEqual(unregistered(catalogue, state), ['isbn-2', 'isbn-3'])


if __name__ == '__main__':
    unittest.main()
