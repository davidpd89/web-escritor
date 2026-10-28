import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ManifestEditorialSafety(unittest.TestCase):
    def test_visible_manifest_copy(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        fields = [(key, manifest.get(key)) for key in ('name', 'short_name', 'description')]
        for index, shortcut in enumerate(manifest.get('shortcuts', [])):
            fields.extend((f'shortcuts[{index}].{key}', shortcut.get(key)) for key in ('name', 'short_name', 'description'))
        self.assertGreater(len(fields), 3, 'manifest.json: no hay textos de accesos directos')
        for field, value in fields:
            with self.subTest(field=field):
                self.assertIsInstance(value, str, f'manifest.json {field}: no es texto')
                self.assertTrue(value.strip(), f'manifest.json {field}: texto vacío')
                self.assertIsNone(re.search(r'<[^>]+>|[\x00-\x08\x0b-\x1f\x7f]', value), f'manifest.json {field}: contenido HTML o control: {value!r}')
                self.assertIsNone(re.search(r'javascript\s*:|data\s*:\s*text/html|\b(?:TODO|FIXME|LOREM IPSUM|PENDIENTE)\b', value, re.I), f'manifest.json {field}: contenido inseguro o provisional: {value!r}')

if __name__ == '__main__':
    unittest.main()