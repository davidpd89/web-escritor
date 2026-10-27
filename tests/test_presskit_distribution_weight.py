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


class DistributionWeight(unittest.TestCase):
    def test_real_package_respects_transfer_budget(self):
        manifest = load('press-kit/package-manifest.json')
        book = load(manifest['bookFacts'])
        author = load(manifest['authorFacts'])
        budget = manifest['maxPackageBytes']
        self.assertGreater(budget, 0, 'Kit de prensa: presupuesto maxPackageBytes ausente')

        approved_assets = [
            item for item in manifest['assets']
            if item.get('releaseStatus') == 'approved'
        ]
        distribution_manifest = dict(manifest)
        distribution_manifest['assets'] = approved_assets
        payload, _ = builder.build_bytes(distribution_manifest, book, author)

        self.assertLessEqual(
            len(payload), budget,
            f'Kit de prensa: ZIP de {len(payload)} bytes supera el presupuesto de {budget} bytes'
        )

        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for item in approved_assets:
                name = item['archivePath']
                with self.subTest(asset=name):
                    info = archive.getinfo(name)
                    source_size = (ROOT / item['source']).stat().st_size
                    self.assertEqual(info.file_size, source_size, f'Kit de prensa: tamaño original incorrecto para {name}')
                    self.assertLessEqual(info.compress_size, info.file_size + 256, f'Kit de prensa: sobrecoste de compresión excesivo en {name}')

            blocked = [
                item['archivePath'] for item in manifest['assets']
                if item.get('releaseStatus') != 'approved'
            ]
            for name in blocked:
                self.assertNotIn(name, archive.namelist(), f'Kit de prensa: recurso no aprobado distribuido: {name}')


if __name__ == '__main__':
    unittest.main()
