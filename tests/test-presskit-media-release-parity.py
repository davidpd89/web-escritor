import importlib.util
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('press_builder', ROOT / 'scripts/build-press-kit.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
load = lambda p: json.loads((ROOT / p).read_text())

class MediaReleaseParity(unittest.TestCase):
    def test_exposed_media_has_correct_status(self):
        manifest = load('press-kit/package-manifest.json')
        book = load('press-kit/las-manecillas-del-recuerdo.json')
        assets = {a['source']: a for a in manifest['assets']}
        media = book['press']
        for field in ('mockup3D', 'socialCardHorizontal'):
            with self.subTest(field=field):
                source = 'assets/' + Path(urlsplit(media[field]).path).name
                self.assertIn(source, assets)
                self.assertEqual(assets[source]['releaseStatus'], 'approved')
        blocked = [a for a in manifest['assets'] if a['releaseStatus'] != 'approved']
        self.assertTrue(blocked)
        self.assertIsNone(media['coverHighRes'])
        self.assertEqual(media['coverReleaseStatus'], 'blocked-pending-editorial-clearance')
        self.assertTrue(all(a['releaseStatus'] == media['coverReleaseStatus'] for a in blocked))

    def test_unreleased_media_not_advertised_in_readme(self):
        manifest = load('press-kit/package-manifest.json')
        book = load('press-kit/las-manecillas-del-recuerdo.json')
        author = load('press-kit/david-porto-diaz.json')
        readme = builder.make_readme(book, author, manifest).decode('utf-8')
        for asset in manifest['assets']:
            with self.subTest(source=asset['source']):
                if asset['releaseStatus'] == 'approved':
                    self.assertIn(asset['archivePath'], readme)
                else:
                    self.assertNotIn(asset['archivePath'], readme)

if __name__ == '__main__':
    unittest.main()