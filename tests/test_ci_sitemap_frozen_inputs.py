from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build-sitemap.py'

class SitemapDeterminismTest(unittest.TestCase):
    def test_filesystem_mtime_does_not_change_sitemap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html = root / 'index.html'
            output = root / 'sitemap.xml'
            html.write_text('<html><head><link rel="canonical" href="https://davidportodiaz.com/"><script type="application/ld+json">{"@type":"WebPage","dateModified":"2026-10-20"}</script></head><body><h1>Prueba</h1></body></html>', encoding='utf-8')
            versions = []
            for timestamp, zone in [(946684800, 'UTC'), (1893456000, 'Europe/Madrid'), (946684800, 'America/Los_Angeles')]:
                os.utime(html, (timestamp, timestamp))
                env = dict(os.environ, TZ=zone)
                result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), '--output', str(output)], cwd=root, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                versions.append(output.read_bytes())
            self.assertEqual(versions[0], versions[1])
            self.assertEqual(versions[1], versions[2])
            self.assertIn(b'2026-10-20', versions[0])
            result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), '--output', str(output), '--check'], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == '__main__':
    unittest.main()