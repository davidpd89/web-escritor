import hashlib
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


class ArchiveContentParity(unittest.TestCase):
    def test_archive_contains_exact_approved_sources(self):
        manifest = load('press-kit/package-manifest.json')
        book = load(manifest['bookFacts'])
        author = load(manifest['authorFacts'])
        distribution = dict(manifest)
        distribution['assets'] = [
            item for item in manifest['assets']
            if item.get('releaseStatus') == 'approved'
        ]
        payload, checksums = builder.build_bytes(distribution, book, author)

        expected_files = {
            item['archivePath']: ROOT / item['source']
            for item in distribution['documents'] + distribution['assets']
        }
        expected_names = set(expected_files) | {
            'README.txt', 'MANIFEST.json', 'CHECKSUMS_SHA256.txt'
        }

        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), len(set(names)), 'Kit de prensa: nombres de archivo duplicados en ZIP')
            self.assertEqual(set(names), expected_names, f'Kit de prensa: contenido inesperado o ausente: {set(names) ^ expected_names}')
            self.assertIsNone(archive.testzip(), 'Kit de prensa: recurso comprimido corrupto')

            for name, source in expected_files.items():
                with self.subTest(file=name):
                    self.assertEqual(archive.read(name), source.read_bytes(), f'Kit de prensa: {name} no coincide con {source.relative_to(ROOT)}')

            actual_checksums = dict(checksums)
            for name in expected_names - {'CHECKSUMS_SHA256.txt'}:
                with self.subTest(checksum=name):
                    digest = hashlib.sha256(archive.read(name)).hexdigest()
                    self.assertEqual(actual_checksums.get(name), digest, f'Kit de prensa: checksum incorrecto para {name}')

            self.assertEqual(
                json.loads(archive.read('MANIFEST.json').decode('utf-8')),
                distribution,
                'Kit de prensa: MANIFEST.json no describe el contenido distribuido'
            )


if __name__ == '__main__':
    unittest.main()
