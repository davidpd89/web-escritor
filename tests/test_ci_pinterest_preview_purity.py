from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build-reading-pinterest-rss.py'

def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

class PinterestPreviewPurityTest(unittest.TestCase):
    def test_preview_cannot_modify_publication_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            shutil.copy2(ROOT / 'data/reading-pinterest-boards.json', root / 'data/reading-pinterest-boards.json')
            (root / 'data/reading-catalogue.json').write_text(json.dumps({'libros': [], 'libro_categorias': []}), encoding='utf-8')
            before = snapshot(root)
            command = [sys.executable, str(SCRIPT), '--root', str(root), '--preview', '--today', '2026-10-20']
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertIn('queue', report)
            self.assertIn('feeds', report)
            self.assertEqual(before, snapshot(root), '--preview ha modificado ficheros')
            self.assertFalse((root / 'data/reading-pinterest-state.json').exists())

if __name__ == '__main__':
    unittest.main()