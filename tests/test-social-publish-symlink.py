"""A poisoned remote tree must not turn the publisher into an arbitrary-file writer."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/research'))
import gpt_social_publish as pub

NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


def git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


@unittest.skipUnless(shutil.which('git') and hasattr(Path, 'symlink_to'), 'git and symlinks required')
class GitPathSafetyTests(unittest.TestCase):
    def test_remote_symlink_cannot_write_outside_dedicated_clone(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d); bare = tmp / 'origin.git'; seed = tmp / 'seed'
            git(tmp, 'init', '--bare', '-b', 'main', str(bare))
            git(tmp, 'clone', '-q', str(bare), str(seed))
            git(seed, 'config', 'user.email', 'qa@example.invalid')
            git(seed, 'config', 'user.name', 'QA')
            (seed / 'redes-sociales').mkdir()
            outside = tmp / 'outside.txt'
            outside.write_text('KEEP', encoding='utf-8')
            try:
                (seed / pub.REL).symlink_to(outside)
            except OSError as exc:
                if sys.platform == 'win32' and getattr(exc, 'winerror', None) == 1314:
                    self.skipTest('Windows no permite crear enlaces simbólicos sin los privilegios necesarios')
                raise
            git(seed, 'add', '.')
            git(seed, 'commit', '-qm', 'malicious symlink')
            git(seed, 'push', '-q', 'origin', 'HEAD:main')
            source = tmp / 'source.json'
            data = json.loads((ROOT / pub.REL).read_text(encoding='utf-8'))
            data['generated_at'] = NOW.isoformat().replace('+00:00', 'Z')
            source.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaises(pub.PublishError):
                pub.publish(source, tmp / 'clone', str(bare), now=NOW)
            self.assertEqual(outside.read_text(encoding='utf-8'), 'KEEP')


if __name__ == '__main__':
    unittest.main()
