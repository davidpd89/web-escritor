import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_guid_qa', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FeedGuidUniqueness(unittest.TestCase):
    def test_duplicate_canonical_is_emitted_once(self):
        url = 'https://davidportodiaz.com/cuaderno/prueba/'
        items = [
            {'url': url, 'title': 'Primera versión', 'date': '2026-10-20'},
            {'url': url, 'title': 'Segunda versión', 'date': '2026-10-21'},
        ]
        root = ET.fromstring(mod.build_feed_bytes(items))
        guids = [node.text for node in root.findall('./channel/item/guid')]
        self.assertEqual(guids, [url], 'Un artículo no puede aparecer dos veces en RSS')

if __name__ == '__main__':
    unittest.main()