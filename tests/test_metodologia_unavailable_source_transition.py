import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))

class UnavailableSourceTransition(unittest.TestCase):
    def test_official_channel_is_not_clickable(self):
        fixture = copy.deepcopy(RAW)
        record = copy.deepcopy(fixture['publishers'][0])
        record['status'] = 'unknown'
        record['direct_submission'] = False
        record['submission_email'] = None
        record['unavailable_urls'] = [record['submission_url']]
        fixture['publishers'] = [record]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'fixture.json'
            output = root / 'out'
            source.write_text(json.dumps(fixture, ensure_ascii=False), encoding='utf-8')
            result = subprocess.run(['python3', 'scripts/build-editoriales.py', '--data', str(source), '--output', str(output), '--today', '2026-10-24'], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = (output / 'editoriales' / record['slug'] / 'index.html').read_text(encoding='utf-8')
            self.assertIn('El canal oficial no está disponible.', page)
            self.assertNotIn('Comprobar las instrucciones oficiales</a>', page)
            self.assertIn('enlace no disponible', page)
            self.assertNotIn('mailto:', page)

if __name__ == '__main__':
    unittest.main()