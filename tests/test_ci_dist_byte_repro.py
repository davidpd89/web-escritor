from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build-public-dist.py'

def digest_tree(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob('*')) if p.is_file()}

class DistributionReproducibilityTest(unittest.TestCase):
    def test_two_builds_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'dist'
            command = [sys.executable, str(SCRIPT), '--root', str(ROOT), '--out', str(out)]
            versions = []
            manifests = []
            for _ in range(2):
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                version = digest_tree(out)
                self.assertTrue(version)
                versions.append(version)
                manifest = out.with_name(out.name + '-manifest.json')
                self.assertTrue(manifest.is_file())
                manifests.append(manifest.read_bytes())
            self.assertEqual(versions[0], versions[1], 'La distribución cambia entre builds idénticos')
            self.assertEqual(manifests[0], manifests[1], 'El manifiesto cambia entre builds idénticos')
            forbidden = [name for name in versions[0] if name.startswith(('.github/', 'tests/', 'qa/'))]
            self.assertEqual(forbidden, [], f'Ficheros internos publicados: {forbidden}')

if __name__ == '__main__':
    unittest.main()