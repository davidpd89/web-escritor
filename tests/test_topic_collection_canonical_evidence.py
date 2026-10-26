import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('topics', ROOT / 'scripts/build-topic-collections.py')
topics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topics)

class CanonicalEvidence(unittest.TestCase):
    def test_expected_url_in_comment_does_not_authorize_wrong_canonical(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'cuaderno/articulo/index.html'
            page.parent.mkdir(parents=True)
            page.write_text('<!doctype html><html><head><link rel="canonical" href="https://davidportodiaz.com/cuaderno/otra-pagina/"><!-- https://davidportodiaz.com/cuaderno/articulo/ --></head><body><main><h1>Artículo</h1></main></body></html>', encoding='utf-8')
            ready = [{'slug': 'coleccion-prueba', 'items': [{'url': '/cuaderno/articulo/', 'title': 'Artículo', 'description': 'Prueba', 'type': 'articulo'}]}]
            with self.assertRaises(topics.ValidationError):
                topics.check_repo(root, ready)

    def test_correct_canonical_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'cuaderno/articulo/index.html'
            page.parent.mkdir(parents=True)
            page.write_text('<html><head><link rel="canonical" href="https://davidportodiaz.com/cuaderno/articulo/"></head><body><h1>Artículo</h1></body></html>', encoding='utf-8')
            ready = [{'slug': 'coleccion-prueba', 'items': [{'url': '/cuaderno/articulo/'}]}]
            self.assertIsNone(topics.check_repo(root, ready))

if __name__ == '__main__':
    unittest.main()