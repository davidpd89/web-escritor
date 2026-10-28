import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('press_builder', ROOT / 'scripts/build-press-kit.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


class PublishedCopyIntegrity(unittest.TestCase):
    def test_readme_preserves_editorial_copy(self):
        book = load('press-kit/las-manecillas-del-recuerdo.json')
        author = load('press-kit/david-porto-diaz.json')
        manifest = load('press-kit/package-manifest.json')
        readme = builder.make_readme(book, author, manifest).decode('utf-8')

        expected = {
            'titulo': book['title'],
            'autor': author['name'],
            'sinopsis': book['synopsis']['short'],
            'biografia': author['shortBio'],
            'editorial': book['publisher'],
            'isbn': book['isbn'],
            'publicacion': book['publicationDate'],
        }
        for field, value in expected.items():
            with self.subTest(field=field):
                self.assertIsInstance(value, str)
                self.assertTrue(value.strip(), f'Kit de prensa: {field} vacío en la fuente')
                self.assertIn(value, readme, f'Kit de prensa README.txt: falta el contenido de {field}')

        for marker in ('TODO', 'TBD', 'Lorem ipsum', 'Texto pendiente', 'Sinopsis pendiente'):
            with self.subTest(marker=marker):
                self.assertNotIn(marker.casefold(), readme.casefold(), f'Kit de prensa README.txt: texto de relleno {marker!r}')


if __name__ == '__main__':
    unittest.main()
