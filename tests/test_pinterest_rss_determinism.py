import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PinterestDeterminism(unittest.TestCase):
    def test_repeated_builds_are_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            for name in ['scripts', 'data', 'assets']:
                source = ROOT / name
                if source.exists():
                    shutil.copytree(source, tmp / name)
            config = tmp / 'data/reading-pinterest-boards.json'
            data = json.loads(config.read_text(encoding='utf-8'))
            data['rss_enabled'] = True
            config.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            command = [sys.executable, 'scripts/build-reading-pinterest-rss.py', '--assign', '--today', '2026-10-20']
            def build():
                subprocess.run(command, cwd=tmp, check=True, capture_output=True, text=True)
                return {str(p.relative_to(tmp)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp / 'assets/pinterest/feeds').rglob('*.xml')}
            first = build()
            self.assertTrue(first, 'La generación debe producir al menos un feed')
            self.assertEqual(first, build())

if __name__ == '__main__':
    unittest.main()