import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PinterestRSSIdempotency(unittest.TestCase):
    def test_two_identical_builds(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'repo'
            shutil.copytree(ROOT / 'scripts', target / 'scripts')
            shutil.copytree(ROOT / 'data', target / 'data')
            shutil.copytree(ROOT / 'assets/pinterest', target / 'assets/pinterest')
            boards = target / 'data/reading-pinterest-boards.json'
            config = json.loads(boards.read_text(encoding='utf-8'))
            config['rss_enabled'] = True
            boards.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
            command = ['python', 'scripts/build-reading-pinterest-rss.py', '--assign', '--today', '2026-10-20']
            snapshots = []
            for _ in range(2):
                subprocess.run(command, cwd=target, check=True, timeout=60)
                snapshots.append({str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((target / 'assets/pinterest').rglob('*.xml'))})
            self.assertTrue(snapshots[0], 'No se generaron feeds')
            self.assertEqual(snapshots[0], snapshots[1])


if __name__ == '__main__':
    unittest.main()