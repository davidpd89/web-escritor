import copy
import json
import subprocess
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
TODAY = date(2026, 10, 24)

class StaleBoundaryTest(unittest.TestCase):
    def test_exact_boundary_in_both_surfaces(self):
        for age in [89, 90, 91]:
            with self.subTest(age=age), tempfile.TemporaryDirectory() as directory:
                fixture = copy.deepcopy(RAW)
                record = copy.deepcopy(fixture['publishers'][0])
                record['verified_at'] = (TODAY - timedelta(days=age)).isoformat()
                fixture['publishers'] = [record]
                root = Path(directory)
                source = root / 'input.json'
                output = root / 'output'
                source.write_text(json.dumps(fixture, ensure_ascii=False), encoding='utf-8')
                result = subprocess.run(['python3', 'scripts/build-editoriales.py', '--data', str(source), '--output', str(output), '--today', TODAY.isoformat()], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                index = (output / 'editoriales/index.html').read_text(encoding='utf-8')
                detail = (output / 'editoriales' / record['slug'] / 'index.html').read_text(encoding='utf-8')
                self.assertEqual('Verificación antigua:' in index, age > 90)
                self.assertEqual('Revisión recomendada:' in detail, age > 90)

if __name__ == '__main__':
    unittest.main()