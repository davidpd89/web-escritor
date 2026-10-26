import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_placeholders', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

PLACEHOLDER = re.compile(r'\b(?:TODO|FIXME|TBC|TBD|lorem\s+ipsum|texto\s+de\s+prueba|pendiente\s+de\s+(?:completar|redactar)|insertar\s+(?:título|titulo|texto)\s+aquí)\b|\[\[pendiente\]\]', re.I)

class EditorialPlaceholderTests(unittest.TestCase):
    def test_real_feed_metadata_has_no_placeholders(self):
        items, _ = feed.collect_items()
        self.assertTrue(items, 'cuaderno/feed.xml: no se han descubierto artículos')
        for item in items:
            for field in ('title', 'description'):
                with self.subTest(page=item['path'], field=field):
                    value = item.get(field)
                    self.assertTrue(value and value.strip(), f"{item['path']}: {field} vacío")
                    match = PLACEHOLDER.search(value)
                    self.assertIsNone(match, f"{item['path']}: {field} contiene texto provisional {match.group(0)!r}" if match else '')

if __name__ == '__main__':
    unittest.main()