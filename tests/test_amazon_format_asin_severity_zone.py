import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('amazon_asin_severity', ROOT / 'scripts/audit-amazon-links.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

class FormatAsinSeverity(unittest.TestCase):
    def test_conflicting_verified_format_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            (root / 'index.html').write_text('<main>Libros</main>', encoding='utf-8')
            book = {'id': 'lib-1', 'slug': 'libro', 'titulo': 'Libro', 'estado': 'publicado', 'isbn13': '9788498382372', 'url_amazon_afiliada': 'https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21', 'formatos_compra': [{'formato': 'ebook', 'url': 'https://www.amazon.es/dp/B08CYCPBZN?tag=davidporto-21', 'fuente_url': 'https://www.amazon.es/dp/B0GB6LGQFH'}]}
            (root / 'data/reading-catalogue.json').write_text(json.dumps({'libros': [book]}), encoding='utf-8')
            result = module.audit(root, 'davidporto-21')
            self.assertTrue(any(x.get('type') == 'fuente_ASIN_diferente' for x in result['manual_review']))
            self.assertTrue(result['errors'], 'La discrepancia documental no bloquea la auditoría')

if __name__ == '__main__':
    unittest.main()
