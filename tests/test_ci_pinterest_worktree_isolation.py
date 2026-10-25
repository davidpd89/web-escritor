import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('data/reading-pinterest-boards.json', 'scripts/build-reading-pinterest-rss.py', 'scripts/export-reading-pinterest-plan.py')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class PinterestWorktreeIsolation(unittest.TestCase):
    def test_preview_does_not_mutate_source_repository(self):
        originals = {name: digest(ROOT / name) for name in FILES}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'repo'
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('.git', 'node_modules', '.venv', '__pycache__'))
            result = subprocess.run([sys.executable, 'scripts/build-reading-pinterest-rss.py', '--preview', '--today', '2026-10-20'], cwd=target, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name, expected in originals.items():
            with self.subTest(path=name):
                self.assertEqual(digest(ROOT / name), expected)

if __name__ == '__main__':
    unittest.main()