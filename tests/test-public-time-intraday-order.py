import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check-public-time-semantics.py'

def fixture(root, end):
    script = root / 'scripts/check-public-time-semantics.py'
    script.parent.mkdir(parents=True)
    shutil.copyfile(SCRIPT, script)
    data = root / 'data/content-registry.json'
    data.parent.mkdir(parents=True)
    data.write_text(json.dumps({'entries': [
        {'sourceFile':'cuaderno/prueba/index.html','status':'public'}
    ]}), encoding='utf-8')
    page = root / 'cuaderno/prueba/index.html'
    page.parent.mkdir(parents=True)
    event = {'@context':'https://schema.org','@type':'Event',
        'name':'Prueba temporal',
        'startDate':'2020-01-10T10:00:00+02:00',
        'endDate':end}
    page.write_text('<html><head><script type="application/ld+json">' +
        json.dumps(event) + '</script></head><body></body></html>', encoding='utf-8')
    return script

class IntradayOrderTests(unittest.TestCase):
    def run_case(self, end):
        with tempfile.TemporaryDirectory() as tmp:
            script = fixture(Path(tmp), end)
            return subprocess.run([sys.executable, str(script)],
                text=True, capture_output=True, timeout=15)

    def test_valid_order_is_accepted(self):
        p = self.run_case('2020-01-10T11:00:00+02:00')
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_reversed_same_day_is_rejected(self):
        p = self.run_case('2020-01-10T09:59:00+02:00')
        self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn('endDate', p.stdout + p.stderr)

    def test_reversed_offset_instants_are_rejected(self):
        p = self.run_case('2020-01-10T07:59:00Z')
        self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)

if __name__ == '__main__':
    unittest.main()
