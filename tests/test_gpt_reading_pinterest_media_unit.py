import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_pinterest_media', ROOT / 'scripts/build-reading-pinterest-rss.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PinterestMediaTests(unittest.TestCase):
    def test_real_feed_images_have_valid_media_types(self):
        config_path = ROOT / 'data/reading-pinterest-config.json'
        if not config_path.is_file():
            self.skipTest('No se ha localizado la configuración del feed en esta ruta')
        config = json.loads(config_path.read_text(encoding='utf-8'))
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        state_path = ROOT / 'data/reading-pinterest-state.json'
        if not state_path.is_file():
            self.skipTest('No se ha localizado el estado del feed en esta ruta')
        state = json.loads(state_path.read_text(encoding='utf-8'))
        files, entries = module.expected_files(ROOT, config, data, state, date(2026, 10, 26))
        self.assertIsInstance(files, dict)
        self.assertIsInstance(entries, list)
        allowed = module.ALLOWED_IMAGE_EXTENSIONS
        for path, xml in files.items():
            with self.subTest(feed=str(path)):
                document = ET.fromstring(xml)
                for item in document.findall('.//item'):
                    media = item.find('{%s}content' % module.MEDIA_NS)
                    self.assertIsNotNone(media, str(path) + ': item sin media:content')
                    image_url = media.get('url', '')
                    parsed = urlsplit(image_url)
                    self.assertEqual(parsed.scheme, 'https', str(path) + ': ' + image_url)
                    self.assertEqual(parsed.hostname, 'davidportodiaz.com', str(path) + ': ' + image_url)
                    local = ROOT / parsed.path.lstrip('/')
                    self.assertTrue(local.is_file(), str(path) + ': imagen inexistente ' + parsed.path)
                    self.assertEqual(media.get('type'), allowed.get(local.suffix.lower()), str(path) + ': MIME de ' + parsed.path)

if __name__ == '__main__':
    unittest.main()
