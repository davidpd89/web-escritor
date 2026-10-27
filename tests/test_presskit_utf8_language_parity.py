import importlib.util
import io
import json
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('press_builder', ROOT / 'scripts/build-press-kit.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


class Utf8LanguageParity(unittest.TestCase):
    def test_published_texts_keep_language_and_unicode(self):
        manifest = load('press-kit/package-manifest.json')
        book = load(manifest['bookFacts'])
        author = load(manifest['authorFacts'])
        self.assertEqual(book['language'], 'es-ES', 'Ficha del libro: idioma distinto de es-ES')

        distribution = dict(manifest)
        distribution['assets'] = []
        payload, _ = builder.build_bytes(distribution, book, author)

        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            readme = archive.read('README.txt').decode('utf-8', errors='strict')
            self.assertIn('DÍAZ', readme, 'README.txt: apellido sin acento')
            self.assertIn('SINOPSIS BREVE', readme, 'README.txt: encabezado editorial ausente')
            self.assertIn('BIO BREVE', readme, 'README.txt: encabezado biográfico ausente')

            for item in manifest['documents']:
                with self.subTest(document=item['archivePath']):
                    raw = archive.read(item['archivePath'])
                    packaged = json.loads(raw.decode('utf-8', errors='strict'))
                    original = load(item['source'])
                    self.assertEqual(packaged, original, f'Kit de prensa: contenido Unicode alterado en {item["archivePath"]}')

            author_doc = next(item for item in manifest['documents'] if item['source'] == manifest['authorFacts'])
            packaged_author = json.loads(archive.read(author_doc['archivePath']).decode('utf-8'))
            self.assertEqual(packaged_author['name'], author['name'], 'Kit de prensa: nombre del autor alterado')
            self.assertIn('Díaz', packaged_author['name'], 'Kit de prensa: pérdida del acento en Díaz')


if __name__ == '__main__':
    unittest.main()
