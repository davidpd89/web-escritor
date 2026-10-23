from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build-reading-pinterest-rss.py'

class PinterestTimezoneTest(unittest.TestCase):
    def test_fixed_date_is_timezone_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            shutil.copy2(ROOT / 'data/reading-pinterest-boards.json', root / 'data/reading-pinterest-boards.json')
            (root / 'data/reading-catalogue.json').write_text(json.dumps({'libros': [], 'libro_categorias': []}), encoding='utf-8')
            outputs = []
            for zone in ['UTC', 'Europe/Madrid', 'America/Los_Angeles', 'Pacific/Kiritimati']:
                env = dict(os.environ, TZ=zone, PYTHONHASHSEED='0')
                result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), '--preview', '--today', '2026-10-20'], cwd=root, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, f'{zone}: {result.stderr}')
                outputs.append(json.loads(result.stdout))
            for output in outputs[1:]:
                self.assertEqual(output, outputs[0])

if __name__ == '__main__':
    unittest.main()